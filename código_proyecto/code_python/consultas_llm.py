from pathlib import Path
import json
import re
import pickle

import faiss
import joblib
import networkx as nx
import numpy as np
import pandas as pd
import psycopg2
from llama_cpp import Llama
from sklearn.preprocessing import normalize


LLM = None


# ==========================================================
# RUTAS Y MODELO
# ==========================================================

def _rutas_base():
    carpeta_codigo = Path(__file__).resolve().parent
    carpeta_proyecto = carpeta_codigo.parent

    return {
        "carpeta_codigo": carpeta_codigo,
        "carpeta_proyecto": carpeta_proyecto,
        "modelo": carpeta_proyecto / "modelos" / "modelos" / "Llama-3.2-3B-Instruct-Q4_K_M.gguf",
        "contexto": carpeta_codigo / "contexto_llm_avance5.txt",
        "grafo": carpeta_codigo / "salidas_grafo" / "grafo_metricas_mensuales.pkl",
        "faiss": carpeta_codigo / "salidas_vectoriales" / "hgm_cie_mensual.faiss",
        "vectorizador": carpeta_codigo / "salidas_vectoriales" / "hgm_vectorizador_tfidf.joblib",
        "svd": carpeta_codigo / "salidas_vectoriales" / "hgm_reductor_svd.joblib",
        "corpus": carpeta_codigo / "salidas_vectoriales" / "hgm_corpus_cie_mensual.csv",
    }


def _obtener_llm():
    global LLM
    rutas = _rutas_base()

    if LLM is None:
        print("Cargando modelo LLaMA...")
        LLM = Llama(
            model_path=str(rutas["modelo"]),
            n_ctx=8192,
            n_threads=8,
            n_batch=128,
            logits_all=False,
            verbose=False
        )

    return LLM


def _leer_contexto():
    rutas = _rutas_base()
    return rutas["contexto"].read_text(encoding="utf-8")


def _reparar_json_basico(texto_json):
    texto_json = texto_json.strip()

    # Quitar comas finales antes de cerrar objetos o listas.
    texto_json = re.sub(r",\s*([}\]])", r"\1", texto_json)

    # Insertar coma faltante entre campos JSON consecutivos.
    # Ejemplo: {"parametros":{} "explicacion":"..."}
    texto_json = re.sub(
        r"([}\]\"])\s*(\"[A-Za-z_][A-Za-z0-9_]*\"\s*:)",
        r"\1,\2",
        texto_json
    )

    return texto_json


def _extraer_json(texto):
    texto = texto.strip()

    if texto.startswith("```"):
        texto = texto.replace("```json", "").replace("```", "").strip()

    inicio = texto.find("{")
    fin = texto.rfind("}")

    if inicio == -1 or fin == -1 or fin <= inicio:
        raise ValueError(f"No se encontró JSON en la respuesta del modelo:\n{texto}")

    texto_json = texto[inicio:fin + 1]

    try:
        return json.loads(texto_json)
    except json.JSONDecodeError:
        texto_reparado = _reparar_json_basico(texto_json)
        return json.loads(texto_reparado)


def _valor_simple(valor):
    if pd.isna(valor):
        return None
    if isinstance(valor, (np.integer,)):
        return int(valor)
    if isinstance(valor, (np.floating,)):
        return float(valor)
    return valor


def _df_a_resultado(df, max_filas=20):
    df_preview = df.head(max_filas).copy()
    df_preview = df_preview.where(pd.notna(df_preview), None)

    return {
        "tipo_resultado": "tabla",
        "filas_totales": int(len(df)),
        "columnas": list(df.columns),
        "vista_previa": df_preview.to_dict(orient="records"),
        "dataframe": df
    }


def _imprimir_tabla(df, max_filas=20):
    if df.empty:
        print("Resultado vacío.")
    else:
        print(df.head(max_filas).to_string(index=False))
    print(f"\nFilas recuperadas: {len(df)}")


def _validar_sql(sql):
    sql_limpio = sql.strip().lower()

    if not sql_limpio.startswith("select"):
        raise ValueError("Solo se permiten consultas SELECT.")

    prohibidas = [
        "insert", "update", "delete", "drop", "alter", "truncate",
        "create", "grant", "revoke", "copy", "execute"
    ]

    for palabra in prohibidas:
        if re.search(rf"\b{palabra}\b", sql_limpio):
            raise ValueError(f"SQL no permitido. Contiene: {palabra}")

    return sql.strip().rstrip(";")


def _ejecutar_sql(sql):
    sql = _validar_sql(sql)

    conn = psycopg2.connect(
        dbname="proyecto_preprocesamiento_CD_VIH",
        user="postgres",
        password="deswa123",
        host="localhost",
        port="5432"
    )

    df = pd.read_sql_query(sql, conn)
    conn.close()

    print("\nBackend: SQL")
    print("Consulta ejecutada:")
    print(sql)
    print("\nResultado:")
    _imprimir_tabla(df)

    resultado = _df_a_resultado(df)
    resultado["sql"] = sql
    return resultado


def _cargar_grafo():
    rutas = _rutas_base()

    with open(rutas["grafo"], "rb") as f:
        return pickle.load(f)


def _normalizar_metrica_grafo(metrica):
    texto = str(metrica or "").lower()

    if "defunc" in texto:
        return "proporcion_defunciones_vih"
    if "consulta" in texto:
        return "proporcion_consultas_vih"
    if "cd4" in texto:
        return "proporcion_cd4_bajo"

    if texto in {
        "proporcion_defunciones_vih",
        "proporcion_consultas_vih",
        "proporcion_cd4_bajo"
    }:
        return texto

    return texto


def _resumen_grafo(G):
    conteo_tipos = {}
    for _, datos in G.nodes(data=True):
        tipo = datos.get("tipo", "SIN_TIPO")
        conteo_tipos[tipo] = conteo_tipos.get(tipo, 0) + 1

    resultado = {
        "tipo_resultado": "grafo_resumen",
        "nodos": G.number_of_nodes(),
        "aristas": G.number_of_edges(),
        "nodos_por_tipo": conteo_tipos
    }

    print("\nBackend: GRAFO")
    print(f"Nodos: {resultado['nodos']}")
    print(f"Aristas: {resultado['aristas']}")
    print("Nodos por tipo:")
    for tipo, total in conteo_tipos.items():
        print(f"- {tipo}: {total}")

    return resultado


def _buscar_mes_grafo(G, parametros):
    anio = parametros.get("anio")
    mes = parametros.get("mes")
    nodo = parametros.get("nodo")

    if nodo is None:
        nodo = f"MES_{int(anio)}_{int(mes):02d}"

    if nodo not in G:
        resultado = {
            "tipo_resultado": "grafo_mes",
            "nodo": nodo,
            "encontrado": False,
            "mensaje": "El nodo solicitado no existe en el grafo."
        }
        print("\nBackend: GRAFO")
        print(resultado["mensaje"])
        return resultado

    atributos = dict(G.nodes[nodo])
    relaciones = []

    for _, destino, datos in list(G.out_edges(nodo, data=True)):
        relaciones.append({
            "origen": nodo,
            "destino": destino,
            "atributos": dict(datos)
        })

    resultado = {
        "tipo_resultado": "grafo_mes",
        "nodo": nodo,
        "encontrado": True,
        "atributos": atributos,
        "relaciones_salientes": relaciones
    }

    print("\nBackend: GRAFO")
    print(f"Nodo consultado: {nodo}")
    print("Atributos principales:")
    for campo in [
        "anio", "mes", "periodo", "proporcion_consultas_vih",
        "proporcion_cd4_bajo", "proporcion_defunciones_vih"
    ]:
        if campo in atributos:
            print(f"- {campo}: {atributos.get(campo)}")

    print("Relaciones salientes:")
    for rel in relaciones[:20]:
        print(f"{rel['origen']} -> {rel['destino']} | {rel['atributos'].get('tipo')}")

    return resultado


def _buscar_periodo_grafo(G, parametros):
    periodo = str(parametros.get("periodo", "")).upper()
    nodo_periodo = f"PERIODO_{periodo}"

    if nodo_periodo not in G:
        resultado = {
            "tipo_resultado": "grafo_periodo",
            "periodo": periodo,
            "encontrado": False,
            "meses": []
        }
        print("\nBackend: GRAFO")
        print(f"No existe el periodo en el grafo: {periodo}")
        return resultado

    meses = list(G.predecessors(nodo_periodo))
    meses = sorted(
        meses,
        key=lambda n: G.nodes[n].get("fecha_orden_mes", 0)
    )

    resultado = {
        "tipo_resultado": "grafo_periodo",
        "periodo": periodo,
        "encontrado": True,
        "total_meses": len(meses),
        "meses": meses
    }

    print("\nBackend: GRAFO")
    print(f"Periodo consultado: {periodo}")
    print(f"Meses asociados: {len(meses)}")
    for mes in meses[:30]:
        print(f"- {mes}")

    return resultado


def _buscar_cambios_grafo(G, parametros):
    metrica = _normalizar_metrica_grafo(parametros.get("metrica"))
    cambio_buscado = str(parametros.get("cambio", "")).lower() or None

    if metrica not in {
        "proporcion_consultas_vih",
        "proporcion_cd4_bajo",
        "proporcion_defunciones_vih"
    }:
        metrica = "proporcion_defunciones_vih"

    campo_cambio = f"cambio_{metrica}"
    campo_delta = f"delta_{metrica}"
    campo_pct_delta = f"pct_delta_{metrica}"

    registros = []

    for origen, destino, datos in G.edges(data=True):
        if datos.get("tipo") != "SIGUIENTE_MES":
            continue

        cambio = datos.get(campo_cambio)
        if cambio_buscado is not None and cambio != cambio_buscado:
            continue

        registros.append({
            "origen": origen,
            "destino": destino,
            "periodo_destino": G.nodes[destino].get("periodo"),
            "valor_destino": G.nodes[destino].get(metrica),
            "delta": datos.get(campo_delta),
            "pct_delta": datos.get(campo_pct_delta),
            "cambio": cambio,
            "fecha_orden_mes_destino": G.nodes[destino].get("fecha_orden_mes")
        })

    registros = sorted(registros, key=lambda r: r.get("fecha_orden_mes_destino") or 0)

    resultado = {
        "tipo_resultado": "grafo_cambios",
        "metrica": metrica,
        "cambio": cambio_buscado,
        "total_transiciones": len(registros),
        "transiciones": registros
    }

    print("\nBackend: GRAFO")
    print(f"Métrica: {metrica}")
    print(f"Cambio filtrado: {cambio_buscado}")
    print(f"Transiciones encontradas: {len(registros)}")

    for r in registros[:20]:
        print(
            f"{r['origen']} -> {r['destino']} | "
            f"cambio={r['cambio']} | "
            f"valor={r['valor_destino']} | "
            f"delta={r['delta']} | "
            f"pct_delta={r['pct_delta']}"
        )

    return resultado


def _ejecutar_grafo(accion, parametros):
    G = _cargar_grafo()

    if accion == "resumen_grafo":
        return _resumen_grafo(G)

    if accion == "buscar_mes":
        return _buscar_mes_grafo(G, parametros)

    if accion == "buscar_periodo":
        return _buscar_periodo_grafo(G, parametros)

    if accion in ["buscar_cambios", "buscar_cambio", "buscar_deltas"]:
        return _buscar_cambios_grafo(G, parametros)

    print("\nBackend: GRAFO")
    print(f"Acción de grafo no reconocida: {accion}")

    return {
        "tipo_resultado": "grafo_error",
        "accion": accion,
        "mensaje": "Acción de grafo no reconocida."
    }


# ==========================================================
# VECTORIAL FAISS
# ==========================================================

def _ejecutar_vectorial(query, top_k=5):
    rutas = _rutas_base()

    indice = faiss.read_index(str(rutas["faiss"]))
    vectorizador = joblib.load(rutas["vectorizador"])
    svd = joblib.load(rutas["svd"])
    corpus = pd.read_csv(rutas["corpus"])

    top_k = max(1, min(int(top_k), 20))

    q_tfidf = vectorizador.transform([query])
    q_vec = svd.transform(q_tfidf)
    q_vec = normalize(q_vec, norm="l2").astype(np.float32)

    distancias, indices = indice.search(q_vec, top_k)

    resultados = []

    print("\nBackend: VECTORIAL")
    print(f"Consulta vectorial: {query}")
    print("Resultados:")

    for posicion, idx in enumerate(indices[0], start=1):
        fila = corpus.iloc[int(idx)]
        score = float(distancias[0][posicion - 1])

        registro = {
            "posicion": posicion,
            "score": score,
            "doc_id": _valor_simple(fila.get("doc_id")),
            "fecha_orden_mes": _valor_simple(fila.get("fecha_orden_mes")),
            "codigo": _valor_simple(fila.get("codigo")),
            "descripcion_diagnostico": _valor_simple(fila.get("descripcion_diagnostico")),
            "total_registros": _valor_simple(fila.get("total_registros")),
            "vih_flag": _valor_simple(fila.get("vih_flag")),
        }

        resultados.append(registro)

        print(f"\n{posicion}. score={score:.4f}")
        print(f"doc_id: {registro['doc_id']}")
        print(f"fecha_orden_mes: {registro['fecha_orden_mes']}")
        print(f"codigo: {registro['codigo']}")
        print(f"diagnostico: {registro['descripcion_diagnostico']}")
        print(f"total_registros: {registro['total_registros']}")
        print(f"vih_flag: {registro['vih_flag']}")

    return {
        "tipo_resultado": "vectorial",
        "query": query,
        "top_k": top_k,
        "resultados": resultados
    }


# ==========================================================
# FUNCIÓN PRINCIPAL
# ==========================================================

def consultar_llm(pregunta):
    contexto = _leer_contexto()
    llm = _obtener_llm()

    prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
Eres un router de consultas heterogéneas para un proyecto académico de calidad de datos en salud.
Responde únicamente con JSON válido en una sola línea.

{contexto}
<|eot_id|><|start_header_id|>user<|end_header_id|>
Pregunta del usuario:
{pregunta}

Devuelve un único JSON válido.
Formatos permitidos:
{{"backend":"SQL","accion":"consultar","sql":"SELECT ...","explicacion":"..."}}
{{"backend":"GRAFO","accion":"resumen_grafo","parametros":{{}},"explicacion":"..."}}
{{"backend":"GRAFO","accion":"buscar_mes","parametros":{{"anio":2020,"mes":4}},"explicacion":"..."}}
{{"backend":"GRAFO","accion":"buscar_periodo","parametros":{{"periodo":"PANDEMIA"}},"explicacion":"..."}}
{{"backend":"GRAFO","accion":"buscar_cambios","parametros":{{"metrica":"proporcion_defunciones_vih","cambio":"sube"}},"explicacion":"..."}}
{{"backend":"VECTORIAL","accion":"buscar_similitud","query":"...","top_k":5,"explicacion":"..."}}
{{"backend":"PENDIENTE","accion":"no_disponible","explicacion":"..."}}
<|eot_id|><|start_header_id|>assistant<|end_header_id|>
"""

    salida = llm.create_completion(
        prompt=prompt,
        max_tokens=260,
        temperature=0.0,
        top_p=1.0,
        repeat_penalty=1.1,
        stop=["<|eot_id|>"]
    )

    texto_modelo = salida["choices"][0]["text"].strip()

    try:
        plan = _extraer_json(texto_modelo)
    except Exception as e:
        print("\n===== RESPUESTA CRUDA DEL MODELO =====")
        print(texto_modelo)
        print("\nError al interpretar JSON del modelo:")
        print(e)

        return {
            "pregunta": pregunta,
            "backend": "ERROR_JSON",
            "plan": None,
            "resultado": None,
            "respuesta_cruda": texto_modelo,
            "error": str(e)
        }

    backend = plan.get("backend", "PENDIENTE").upper()
    accion = plan.get("accion", "no_disponible")

    print("\n===== PLAN DEL LLM =====")
    print(json.dumps(plan, ensure_ascii=False, indent=2))

    if backend == "SQL":
        resultado = _ejecutar_sql(plan["sql"])

    elif backend == "GRAFO":
        resultado = _ejecutar_grafo(accion, plan.get("parametros", {}))

    elif backend == "VECTORIAL":
        resultado = _ejecutar_vectorial(
            query=plan.get("query", pregunta),
            top_k=int(plan.get("top_k", 5))
        )

    else:
        print("\nBackend: PENDIENTE")
        print(plan.get("explicacion", "La consulta no está disponible."))
        resultado = {
            "tipo_resultado": "pendiente",
            "explicacion": plan.get("explicacion", "La consulta no está disponible.")
        }

    return {
        "pregunta": pregunta,
        "backend": backend,
        "accion": accion,
        "plan": plan,
        "resultado": resultado
    }