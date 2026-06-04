from pathlib import Path
import json
import os

import faiss
import joblib
import numpy as np
import pandas as pd
import psycopg2

from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import normalize

from code_python.config import DB_CONFIG, SALIDA_VECTORIAL


def _valor_json(valor):
    if pd.isna(valor):
        return None
    if isinstance(valor, (np.integer,)):
        return int(valor)
    if isinstance(valor, (np.floating,)):
        return float(valor)
    return valor


def _exportar_faiss_json(df, ruta_json, n_documentos, n_terminos, dimension_vectorial):
    documentos = []

    for registro in df.to_dict(orient="records"):
        documentos.append({
            clave: _valor_json(valor)
            for clave, valor in registro.items()
        })

    datos = {
        "tipo": "indice_faiss_hgm_cie_mensual",
        "resumen": {
            "documentos_vectorizados": int(n_documentos),
            "dimension_tfidf_original": int(n_terminos),
            "dimension_vectorial_final": int(dimension_vectorial),
            "metrica_faiss": "inner_product_con_vectores_l2_normalizados"
        },
        "documentos": documentos
    }

    with open(ruta_json, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)


def crear_corpus_vectorial_hgm_faiss():
    conn = psycopg2.connect(**DB_CONFIG)

    consulta = """
        SELECT
            fecha_orden_mes,
            codigo,
            descripcion_diagnostico,
            total_registros,
            edad_promedio,
            edad_minima,
            edad_maxima,
            total_sexo_masculino,
            total_sexo_femenino,
            pct_sexo_masculino,
            pct_sexo_femenino,
            total_primera_vez,
            total_subsecuente,
            pct_primera_vez,
            pct_subsecuente,
            total_especialidades,
            especialidad_principal,
            vih_flag
        FROM vw_hgm_vector_cie_mensual
        ORDER BY
            fecha_orden_mes,
            codigo,
            descripcion_diagnostico;
    """

    df = pd.read_sql_query(consulta, conn)
    conn.close()

    df = df.reset_index(drop=True)

    df["doc_id"] = df.apply(
        lambda fila: f"HGM_CIE_MENSUAL_{fila['fecha_orden_mes']}_{fila['codigo']}_{fila.name}",
        axis=1
    )

    df["texto_documento"] = (
        "Codigo CIE: "
        + df["codigo"].astype(str)
        + ". Especialidad principal: "
        + df["especialidad_principal"].astype(str)
        + ". : "
        + df["descripcion_diagnostico"].fillna("").astype(str)
        + ". Casos: "
        + df["total_registros"].astype(str)
        + "."
    )
    
    df.loc[df["vih_flag"] == 1, "texto_documento"] = (
        df.loc[df["vih_flag"] == 1, "texto_documento"]
        + " Asociado a VIH."
    )

    corpus = df["texto_documento"].tolist()

    vectorizador = TfidfVectorizer(
        lowercase=True,
        strip_accents="unicode",
        ngram_range=(1, 2),
        min_df=1
    )

    matriz_tfidf = vectorizador.fit_transform(corpus)

    n_documentos = matriz_tfidf.shape[0]
    n_terminos = matriz_tfidf.shape[1]
    n_componentes = min(128, n_documentos - 1, n_terminos - 1)

    svd = TruncatedSVD(n_components=n_componentes, random_state=42)
    vectores = svd.fit_transform(matriz_tfidf)

    vectores = normalize(vectores, norm="l2")
    vectores = vectores.astype(np.float32)

    indice = faiss.IndexFlatIP(vectores.shape[1])
    indice.add(vectores)

    ruta_salida = SALIDA_VECTORIAL
    ruta_salida.mkdir(exist_ok=True)

    ruta_faiss = ruta_salida / "hgm_cie_mensual.faiss"
    ruta_json = ruta_salida / "hgm_cie_mensual_faiss.json"
    ruta_csv = ruta_salida / "hgm_corpus_cie_mensual.csv"
    ruta_jsonl = ruta_salida / "hgm_corpus_cie_mensual.jsonl"

    faiss.write_index(
        indice,
        str(ruta_faiss)
    )

    joblib.dump(
        vectorizador,
        ruta_salida / "hgm_vectorizador_tfidf.joblib"
    )

    joblib.dump(
        svd,
        ruta_salida / "hgm_reductor_svd.joblib"
    )

    df.to_csv(
        ruta_csv,
        index=False,
        encoding="utf-8-sig"
    )

    df.to_json(
        ruta_jsonl,
        orient="records",
        lines=True,
        force_ascii=False
    )

    _exportar_faiss_json(df, ruta_json, n_documentos, n_terminos, vectores.shape[1])
    print("Corpus vectorial HGM generado.")
    print(f"Documentos vectorizados: {len(df)}")
    print(f"Dimension TF-IDF original: {n_terminos}")
    print(f"Dimension vectorial final: {vectores.shape[1]}")
    print(f"Indice FAISS: {ruta_salida / 'hgm_cie_mensual.faiss'}")
    print(f"Metadatos CSV: {ruta_salida / 'hgm_corpus_cie_mensual.csv'}")
    print(f"Corpus JSONL: {ruta_salida / 'hgm_corpus_cie_mensual.jsonl'}")
    print(f"JSON: {ruta_json}")
    
