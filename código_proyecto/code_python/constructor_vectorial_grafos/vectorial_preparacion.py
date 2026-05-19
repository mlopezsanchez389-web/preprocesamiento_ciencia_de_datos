from pathlib import Path
import pickle
import pandas as pd
import psycopg2
from sklearn.feature_extraction.text import TfidfVectorizer

# =========================================================
# CONFIGURACION GENERAL
# =========================================================

HOST = "localhost"
PORT = "5432"
DBNAME = "proyecto_preprocesamiento_CD_VIH"
USER = "postgres"
PASSWORD = "deswa123"

BASE_DIR = Path(__file__).resolve().parent
DATOS_DIR = BASE_DIR / "datos" / "vectorial"
DATOS_DIR.mkdir(parents=True, exist_ok=True)

ARCHIVO_CORPUS_CSV = DATOS_DIR / "corpus_vectorial_mensual.csv"
ARCHIVO_CORPUS_JSON = DATOS_DIR / "corpus_vectorial_mensual.json"
ARCHIVO_INDICE = DATOS_DIR / "indice_vectorial_tfidf.pkl"

# =========================================================
# EXTRACCION DESDE POSTGRESQL
# =========================================================

def obtener_conexion():
    return psycopg2.connect(
        host=HOST,
        port=PORT,
        dbname=DBNAME,
        user=USER,
        password=PASSWORD
    )

def cargar_metricas_integradas() -> pd.DataFrame:
    consulta = """
    SELECT *
    FROM vw_metricas_mensuales_integradas
    ORDER BY fecha_orden_mes;
    """
    conn = obtener_conexion()
    try:
        df = pd.read_sql_query(consulta, conn)
    finally:
        conn.close()
    return df

# =========================================================
# CONSTRUCCION DEL CORPUS
# =========================================================

def valor_texto(x):
    if pd.isna(x):
        return "sin dato"
    return x

def construir_texto_mensual(fila) -> str:
    return (
        f"Periodo {fila['periodo']}. "
        f"Mes {int(fila['mes'])} del año {int(fila['anio'])}. "
        f"Consultas VIH: {int(valor_texto(fila['consultas_vih'])) if valor_texto(fila['consultas_vih']) != 'sin dato' else 'sin dato'}. "
        f"Consultas VIH de primera vez: {int(valor_texto(fila['consultas_vih_primera_vez'])) if valor_texto(fila['consultas_vih_primera_vez']) != 'sin dato' else 'sin dato'}. "
        f"Consultas VIH subsecuentes: {int(valor_texto(fila['consultas_vih_subsecuente'])) if valor_texto(fila['consultas_vih_subsecuente']) != 'sin dato' else 'sin dato'}. "
        f"Muestras totales: {int(valor_texto(fila['muestras_total'])) if valor_texto(fila['muestras_total']) != 'sin dato' else 'sin dato'}. "
        f"CD4 promedio: {valor_texto(fila['cd4_promedio'])}. "
        f"Casos con CD4 bajo: {int(valor_texto(fila['casos_cd4_bajo'])) if valor_texto(fila['casos_cd4_bajo']) != 'sin dato' else 'sin dato'}. "
        f"Proporción de CD4 bajo: {valor_texto(fila['proporcion_cd4_bajo'])}. "
        f"Defunciones totales: {int(valor_texto(fila['total_defunciones'])) if valor_texto(fila['total_defunciones']) != 'sin dato' else 'sin dato'}. "
        f"Defunciones VIH: {int(valor_texto(fila['defunciones_vih'])) if valor_texto(fila['defunciones_vih']) != 'sin dato' else 'sin dato'}. "
        f"Pruebas reactivas: {int(valor_texto(fila['pruebas_reactivas'])) if valor_texto(fila['pruebas_reactivas']) != 'sin dato' else 'sin dato'}. "
        f"Porcentaje de pruebas reactivas en consejería: {valor_texto(fila['pct_reactivas_consejeria'])}. "
        f"Porcentaje de pruebas reactivas en otros programas: {valor_texto(fila['pct_reactivas_otros_programas'])}."
    )

def generar_corpus(df: pd.DataFrame) -> pd.DataFrame:
    df_corpus = df.copy()

    df_corpus["doc_id"] = df_corpus.apply(
        lambda fila: f"mes_{int(fila['anio'])}_{int(fila['mes']):02d}",
        axis=1
    )

    df_corpus["texto"] = df_corpus.apply(construir_texto_mensual, axis=1)

    columnas_salida = [
        "doc_id",
        "fecha_orden_mes",
        "anio",
        "mes",
        "periodo",
        "texto"
    ]

    return df_corpus[columnas_salida]

# =========================================================
# INDICE VECTORIAL
# =========================================================

def construir_indice(df_corpus: pd.DataFrame):
    vectorizer = TfidfVectorizer(
        lowercase=True,
        ngram_range=(1, 2),
        min_df=1
    )
    matriz = vectorizer.fit_transform(df_corpus["texto"].fillna(""))

    indice = {
        "vectorizer": vectorizer,
        "matriz": matriz,
        "documentos": df_corpus
    }
    return indice

def guardar_indice(indice):
    with open(ARCHIVO_INDICE, "wb") as f:
        pickle.dump(indice, f)

# =========================================================
# MAIN
# =========================================================

def main():
    df = cargar_metricas_integradas()
    df_corpus = generar_corpus(df)

    df_corpus.to_csv(ARCHIVO_CORPUS_CSV, index=False, encoding="utf-8-sig")
    df_corpus.to_json(ARCHIVO_CORPUS_JSON, orient="records", force_ascii=False, indent=2)

    indice = construir_indice(df_corpus)
    guardar_indice(indice)

    print("Preparacion vectorial completada correctamente")
    print("Corpus CSV guardado en:", ARCHIVO_CORPUS_CSV)
    print("Corpus JSON guardado en:", ARCHIVO_CORPUS_JSON)
    print("Indice guardado en:", ARCHIVO_INDICE)
    print("Documentos generados:", len(df_corpus))
    print("\nPrimeros 5 documentos:\n")
    print(df_corpus.head(5))

if __name__ == "__main__":
    main()
