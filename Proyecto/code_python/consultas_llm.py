from pathlib import Path
import json
import os
import pickle
import re

import faiss
import joblib
import numpy as np
import pandas as pd
import psycopg2
from llama_cpp import Llama
from sklearn.preprocessing import normalize

from code_python.config import DB_CONFIG, RUTA_MODELO, SALIDA_GRAFO, SALIDA_VECTORIAL


LLM_N_CTX = 8192
LLM_N_THREADS = 8
LLM_N_BATCH = 128
ROUTER_MAX_TOKENS = 260
ROUTER_TEMPERATURE = 0.0
ROUTER_TOP_P = 1.0
ROUTER_REPEAT_PENALTY = 1.1

LLM = None


def _rutas_base():
    carpeta_codigo = Path(__file__).resolve().parent
    return {
        "modelo": RUTA_MODELO,
        "contexto": carpeta_codigo / "contexto_llm.txt",
        "grafo": SALIDA_GRAFO / "grafo_metricas_mensuales.pkl",
        "faiss": SALIDA_VECTORIAL / "hgm_cie_mensual.faiss",
        "vectorizador": SALIDA_VECTORIAL / "hgm_vectorizador_tfidf.joblib",
        "svd": SALIDA_VECTORIAL / "hgm_reductor_svd.joblib",
        "corpus": SALIDA_VECTORIAL / "hgm_corpus_cie_mensual.csv",
    }


def _obtener_llm():
    global LLM

    if LLM is None:
        rutas = _rutas_base()
        print("Cargando modelo LLaMA...")
        LLM = Llama(
            model_path=str(rutas["modelo"]),
            n_ctx=LLM_N_CTX,
            n_threads=LLM_N_THREADS,
            n_batch=LLM_N_BATCH,
            logits_all=False,
            verbose=False
        )

    return LLM


def _conexion_postgres():
    return psycopg2.connect(**DB_CONFIG)


def _extraer_json(texto):
    texto = texto.strip()

    if texto.startswith("```"):
        texto = texto.replace("```json", "").replace("```", "").strip()

    inicio = texto.find("{")
    fin = texto.rfind("}")

    if inicio == -1 or fin == -1 or fin <= inicio:
        raise ValueError(f"No se encontro JSON en la respuesta del modelo:\n{texto}")

    texto_json = texto[inicio:fin + 1]

    try:
        return json.loads(texto_json)
    except json.JSONDecodeError:
        texto_json = re.sub(r",\s*([}\]])", r"\1", texto_json)
        texto_json = re.sub(r"([}\]\"])\s*(\"[A-Za-z_][A-Za-z0-9_]*\"\s*:)", r"\1,\2", texto_json)
        return json.loads(texto_json)


def _limpiar_valor(valor):
    if isinstance(valor, np.integer):
        return int(valor)
    if isinstance(valor, np.floating):
        if np.isnan(valor):
            return None
        return float(valor)
    if pd.isna(valor) if not isinstance(valor, (list, dict, tuple, set)) else False:
        return None
    return valor


def _validar_sql(sql):
    sql = sql.strip().rstrip(";")
    sql_limpio = sql.lower()

    if not sql_limpio.startswith("select"):
        raise ValueError("Solo se permiten consultas SELECT.")

    for palabra in ["insert", "update", "delete", "drop", "alter", "truncate", "create", "copy", "grant", "revoke"]:
        if re.search(rf"\b{palabra}\b", sql_limpio):
            raise ValueError(f"SQL no permitido: {palabra}")

    return sql


def _ajustar_sql(sql):
    sql = sql.replace("SUM(pct_", "AVG(pct_")
    sql = sql.replace("SUM(proporcion_", "AVG(proporcion_")

    if "vw_metricas_mensuales_integradas_sexo" in sql or "vw_metricas_mensuales_integradas_grupo_edad" in sql:
        sql = re.sub(r",\s*AVG\(pct_reactivas_consejeria\)\s+AS\s+\w+", "", sql, flags=re.IGNORECASE)
        sql = re.sub(r",\s*AVG\(pct_reactivas_otros_programas\)\s+AS\s+\w+", "", sql, flags=re.IGNORECASE)

    return sql


def _ejecutar_sql(sql):
    sql = _validar_sql(_ajustar_sql(sql))
    conn = _conexion_postgres()
    df = pd.read_sql_query(sql, conn)
    conn.close()

    print("\nBackend: SQL")
    print(sql)
    print(df.head(20).to_string(index=False) if not df.empty else "Sin registros.")
    print(f"Filas recuperadas: {len(df)}")

    return {
        "tipo_resultado": "tabla",
        "sql": sql,
        "filas_totales": int(len(df)),
        "columnas": list(df.columns),
        "vista_previa": df.head(20).where(pd.notna(df), None).to_dict(orient="records")
    }


def _ejecutar_grafo(accion, parametros):
    rutas = _rutas_base()
    with open(rutas["grafo"], "rb") as f:
        G = pickle.load(f)

    print("\nBackend: GRAFO")

    if accion == "resumen_grafo":
        nodos_por_tipo = {}
        for _, datos in G.nodes(data=True):
            tipo = datos.get("tipo", "SIN_TIPO")
            nodos_por_tipo[tipo] = nodos_por_tipo.get(tipo, 0) + 1

        print(f"Nodos: {G.number_of_nodes()}")
        print(f"Aristas: {G.number_of_edges()}")
        return {
            "tipo_resultado": "grafo_resumen",
            "nodos": G.number_of_nodes(),
            "aristas": G.number_of_edges(),
            "nodos_por_tipo": nodos_por_tipo
        }

    if accion == "buscar_periodo":
        periodo = str(parametros.get("periodo", "")).upper()
        nodo = f"PERIODO_{periodo}"
        meses = sorted(
            list(G.predecessors(nodo)) if nodo in G else [],
            key=lambda n: G.nodes[n].get("fecha_orden_mes", 0)
        )

        print(f"Periodo: {periodo}")
        print(f"Meses encontrados: {len(meses)}")
        return {
            "tipo_resultado": "grafo_periodo",
            "periodo": periodo,
            "meses": meses,
            "total_meses": len(meses)
        }

    anio = parametros.get("anio")
    mes = parametros.get("mes")
    nodo = parametros.get("nodo") or f"MES_{int(anio)}_{int(mes):02d}"

    if nodo not in G:
        print(f"Nodo no encontrado: {nodo}")
        return {"tipo_resultado": "grafo_mes", "nodo": nodo, "encontrado": False}

    atributos = dict(G.nodes[nodo])
    print(f"Nodo: {nodo}")
    print({k: atributos.get(k) for k in ["anio", "mes", "periodo"]})
    return {
        "tipo_resultado": "grafo_mes",
        "nodo": nodo,
        "encontrado": True,
        "atributos": {k: _limpiar_valor(v) for k, v in atributos.items()}
    }


def _ejecutar_vectorial(query, top_k=5):
    rutas = _rutas_base()
    indice = faiss.read_index(str(rutas["faiss"]))
    vectorizador = joblib.load(rutas["vectorizador"])
    svd = joblib.load(rutas["svd"])
    corpus = pd.read_csv(rutas["corpus"])

    top_k = max(1, min(int(top_k), 20))
    q_tfidf = vectorizador.transform([query])
    q_vec = normalize(svd.transform(q_tfidf), norm="l2").astype(np.float32)
    distancias, indices = indice.search(q_vec, top_k)

    resultados = []
    print("\nBackend: VECTORIAL")
    print(f"Consulta: {query}")

    for posicion, idx in enumerate(indices[0], start=1):
        fila = corpus.iloc[int(idx)]
        registro = {
            "posicion": posicion,
            "score": float(distancias[0][posicion - 1]),
            "doc_id": _limpiar_valor(fila.get("doc_id")),
            "fecha_orden_mes": _limpiar_valor(fila.get("fecha_orden_mes")),
            "codigo": _limpiar_valor(fila.get("codigo")),
            "descripcion_diagnostico": _limpiar_valor(fila.get("descripcion_diagnostico")),
            "total_registros": _limpiar_valor(fila.get("total_registros")),
            "vih_flag": _limpiar_valor(fila.get("vih_flag")),
        }
        resultados.append(registro)
        print(f"{posicion}. {registro['codigo']} | score={registro['score']:.4f}")

    return {
        "tipo_resultado": "vectorial",
        "query": query,
        "top_k": top_k,
        "resultados": resultados
    }


def consultar_llm(pregunta):
    rutas = _rutas_base()
    contexto = rutas["contexto"].read_text(encoding="utf-8")
    llm = _obtener_llm()

    prompt = f"""<|start_header_id|>system<|end_header_id|>
Eres un router de consultas heterogeneas para un proyecto academico de calidad de datos en salud.
Responde unicamente con JSON valido en una sola linea.

{contexto}
<|eot_id|><|start_header_id|>user<|end_header_id|>
Pregunta:
{pregunta}

Devuelve un unico JSON valido.
{{"backend":"SQL","accion":"consultar","sql":"SELECT ...","explicacion":"..."}}
{{"backend":"GRAFO","accion":"resumen_grafo","parametros":{{}},"explicacion":"..."}}
{{"backend":"GRAFO","accion":"buscar_mes","parametros":{{"anio":2020,"mes":4}},"explicacion":"..."}}
{{"backend":"GRAFO","accion":"buscar_periodo","parametros":{{"periodo":"PANDEMIA"}},"explicacion":"..."}}
{{"backend":"VECTORIAL","accion":"buscar_similitud","query":"...","top_k":5,"explicacion":"..."}}
{{"backend":"PENDIENTE","accion":"no_disponible","explicacion":"..."}}
<|eot_id|><|start_header_id|>assistant<|end_header_id|>
"""

    salida = llm.create_completion(
        prompt=prompt,
        max_tokens=ROUTER_MAX_TOKENS,
        temperature=ROUTER_TEMPERATURE,
        top_p=ROUTER_TOP_P,
        repeat_penalty=ROUTER_REPEAT_PENALTY,
        stop=["<|eot_id|>"]
    )

    texto_modelo = salida["choices"][0]["text"].strip()

    try:
        plan = _extraer_json(texto_modelo)
    except Exception as error:
        print("\nRespuesta cruda del modelo:")
        print(texto_modelo)
        print(f"Error JSON: {error}")
        return {
            "pregunta": pregunta,
            "backend": "ERROR_JSON",
            "accion": "no_disponible",
            "plan": None,
            "resultado": None,
            "respuesta_cruda": texto_modelo,
            "error": str(error)
        }

    backend = plan.get("backend", "PENDIENTE").upper()
    accion = plan.get("accion", "no_disponible")

    print("\nPlan del LLM:")
    print(json.dumps(plan, ensure_ascii=False, indent=2))

    if backend == "SQL":
        resultado = _ejecutar_sql(plan["sql"])
    elif backend == "GRAFO":
        resultado = _ejecutar_grafo(accion, plan.get("parametros", {}))
    elif backend == "VECTORIAL":
        resultado = _ejecutar_vectorial(plan.get("query", pregunta), plan.get("top_k", 5))
    else:
        print("\nBackend: PENDIENTE")
        print(plan.get("explicacion", "Consulta no disponible."))
        resultado = {"tipo_resultado": "pendiente", "explicacion": plan.get("explicacion")}

    return {
        "pregunta": pregunta,
        "backend": backend,
        "accion": accion,
        "plan": plan,
        "resultado": resultado
    }
