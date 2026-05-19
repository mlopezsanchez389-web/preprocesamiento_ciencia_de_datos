from pathlib import Path
import pickle
import pandas as pd
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt

# =========================================================
# CONFIGURACION GENERAL
# =========================================================

BASE_DIR = Path(__file__).resolve().parent
DATOS_DIR = BASE_DIR / "datos" / "grafo"
RESULTADOS_CSV_DIR = BASE_DIR / "resultados" / "grafo" / "csv"
RESULTADOS_IMG_DIR = BASE_DIR / "resultados" / "grafo" / "imagenes"

DATOS_DIR.mkdir(parents=True, exist_ok=True)
RESULTADOS_CSV_DIR.mkdir(parents=True, exist_ok=True)
RESULTADOS_IMG_DIR.mkdir(parents=True, exist_ok=True)

ARCHIVO_GRAFO = DATOS_DIR / "grafo_metricas_mensuales.gpickle"

# =========================================================
# PREGUNTAS GRAFO
# =========================================================

PREGUNTAS_GRAFO = {
    2: "CD4 y relación temporal con consultas y defunciones",
    7: "Disminución simultánea o divergente entre consultas, pruebas y defunciones",
    8: "Primera vez vs subsecuente y relación con severidad y mortalidad",
    10: "Años con mayor discrepancia entre pruebas, atención y mortalidad",
    19: "Indicadores con desacople entre menor detección y persistencia de desenlaces graves"
}

# =========================================================
# FUNCIONES BASE
# =========================================================

def cargar_grafo():
    with open(ARCHIVO_GRAFO, "rb") as f:
        G = pickle.load(f)
    return G

def obtener_periodo_mes(G, nodo_mes: str):
    for vecino in G.neighbors(nodo_mes):
        attrs = G.nodes[vecino]
        if attrs.get("tipo") == "periodo":
            return vecino
    return None

def extraer_metricas_mes(G, nodo_mes: str) -> dict:
    datos_nodo = G.nodes[nodo_mes]

    hgm = G.get_edge_data(nodo_mes, "HGM", default={})
    vih = G.get_edge_data(nodo_mes, "VIH_RED", default={})
    defunciones = G.get_edge_data(nodo_mes, "DEFUNCIONES", default={})
    pruebas = G.get_edge_data(nodo_mes, "PRUEBAS", default={})

    return {
        "nodo_mes": nodo_mes,
        "fecha_orden_mes": datos_nodo.get("fecha_orden_mes"),
        "anio": datos_nodo.get("anio"),
        "mes": datos_nodo.get("mes"),
        "periodo": obtener_periodo_mes(G, nodo_mes),
        "consultas_vih": hgm.get("consultas_vih"),
        "consultas_vih_primera_vez": hgm.get("consultas_vih_primera_vez"),
        "consultas_vih_subsecuente": hgm.get("consultas_vih_subsecuente"),
        "muestras_total": vih.get("muestras_total"),
        "cd4_promedio": vih.get("cd4_promedio"),
        "casos_cd4_bajo": vih.get("casos_cd4_bajo"),
        "proporcion_cd4_bajo": vih.get("proporcion_cd4_bajo"),
        "total_defunciones": defunciones.get("total_defunciones"),
        "defunciones_vih": defunciones.get("defunciones_vih"),
        "pruebas_reactivas": pruebas.get("pruebas_reactivas"),
        "pct_reactivas_consejeria": pruebas.get("pct_reactivas_consejeria"),
        "pct_reactivas_otros_programas": pruebas.get("pct_reactivas_otros_programas"),
    }

def construir_tabla_metricas(G) -> pd.DataFrame:
    nodos_mes = [n for n, attrs in G.nodes(data=True) if attrs.get("tipo") == "mes"]
    filas = [extraer_metricas_mes(G, nodo) for nodo in nodos_mes]
    df = pd.DataFrame(filas).sort_values("fecha_orden_mes").reset_index(drop=True)
    return df

def signo(x):
    if pd.isna(x):
        return None
    if x < 0:
        return "BAJA"
    if x > 0:
        return "SUBE"
    return "IGUAL"

def minmax_serie(serie: pd.Series) -> pd.Series:
    s = pd.to_numeric(serie, errors="coerce")
    mn = s.min()
    mx = s.max()
    if pd.isna(mn) or pd.isna(mx) or mn == mx:
        return pd.Series(np.zeros(len(s)), index=s.index, dtype="float64")
    return (s - mn) / (mx - mn)

# =========================================================
# RESPUESTAS POR PREGUNTA
# =========================================================

def responder_pregunta_2() -> pd.DataFrame:
    G = cargar_grafo()
    df = construir_tabla_metricas(G)

    df["delta_consultas"] = df["consultas_vih"].diff()
    df["delta_cd4_promedio"] = df["cd4_promedio"].diff()
    df["delta_defunciones"] = df["defunciones_vih"].diff()

    df["cambio_consultas"] = df["delta_consultas"].apply(signo)
    df["cambio_cd4_promedio"] = df["delta_cd4_promedio"].apply(signo)
    df["cambio_defunciones"] = df["delta_defunciones"].apply(signo)

    def clasificar_relacion(fila):
        cambios = [fila["cambio_consultas"], fila["cambio_cd4_promedio"], fila["cambio_defunciones"]]
        if any(c is None for c in cambios):
            return "SIN_REFERENCIA_PREVIA"
        if len(set(cambios)) == 1:
            return "MOVIMIENTO_CONSISTENTE"
        return "MOVIMIENTO_NO_CONSISTENTE"

    df["relacion_temporal"] = df.apply(clasificar_relacion, axis=1)

    columnas = [
        "anio", "mes", "periodo",
        "consultas_vih", "cd4_promedio", "casos_cd4_bajo", "defunciones_vih",
        "cambio_consultas", "cambio_cd4_promedio", "cambio_defunciones",
        "relacion_temporal"
    ]
    return df[columnas]

def responder_pregunta_7() -> pd.DataFrame:
    G = cargar_grafo()
    df = construir_tabla_metricas(G)

    df["delta_consultas"] = df["consultas_vih"].diff()
    df["delta_pct_reactivas"] = df["pct_reactivas_consejeria"].diff()
    df["delta_defunciones"] = df["defunciones_vih"].diff()

    df["cambio_consultas"] = df["delta_consultas"].apply(signo)
    df["cambio_pct_reactivas"] = df["delta_pct_reactivas"].apply(signo)
    df["cambio_defunciones"] = df["delta_defunciones"].apply(signo)

    def clasificar_fila(fila):
        cambios = [
            fila["cambio_consultas"],
            fila["cambio_pct_reactivas"],
            fila["cambio_defunciones"],
        ]
        if any(c is None for c in cambios):
            return "SIN_REFERENCIA_PREVIA"
        if cambios == ["BAJA", "BAJA", "BAJA"]:
            return "DISMINUCION_SIMULTANEA"
        if len(set(cambios)) == 1:
            return "MOVIMIENTO_CONSISTENTE"
        return "DIVERGENTE"

    df["patron"] = df.apply(clasificar_fila, axis=1)

    columnas_salida = [
        "anio", "mes", "periodo",
        "consultas_vih", "pct_reactivas_consejeria", "defunciones_vih",
        "cambio_consultas", "cambio_pct_reactivas", "cambio_defunciones",
        "patron",
    ]
    return df[columnas_salida]

def responder_pregunta_8() -> pd.DataFrame:
    G = cargar_grafo()
    df = construir_tabla_metricas(G)

    total = df["consultas_vih_primera_vez"] + df["consultas_vih_subsecuente"]
    df["prop_primera_vez"] = np.where(total > 0, df["consultas_vih_primera_vez"] / total, np.nan)
    df["prop_subsecuente"] = np.where(total > 0, df["consultas_vih_subsecuente"] / total, np.nan)

    df["delta_prop_primera_vez"] = df["prop_primera_vez"].diff()
    df["delta_cd4_bajo"] = df["casos_cd4_bajo"].diff()
    df["delta_defunciones"] = df["defunciones_vih"].diff()

    df["cambio_prop_primera_vez"] = df["delta_prop_primera_vez"].apply(signo)
    df["cambio_cd4_bajo"] = df["delta_cd4_bajo"].apply(signo)
    df["cambio_defunciones"] = df["delta_defunciones"].apply(signo)

    def clasificar_relacion(fila):
        cambios = [fila["cambio_prop_primera_vez"], fila["cambio_cd4_bajo"], fila["cambio_defunciones"]]
        if any(c is None for c in cambios):
            return "SIN_REFERENCIA_PREVIA"
        if len(set(cambios)) == 1:
            return "MOVIMIENTO_CONSISTENTE"
        return "RELACION_TEMPORAL_MIXTA"

    df["relacion_temporal"] = df.apply(clasificar_relacion, axis=1)

    columnas = [
        "anio", "mes", "periodo",
        "consultas_vih_primera_vez", "consultas_vih_subsecuente",
        "prop_primera_vez", "prop_subsecuente",
        "cd4_promedio", "casos_cd4_bajo", "defunciones_vih",
        "relacion_temporal"
    ]
    return df[columnas]

def responder_pregunta_10() -> pd.DataFrame:
    G = cargar_grafo()
    df = construir_tabla_metricas(G)

    anual = (
        df.groupby("anio", as_index=False)
        .agg(
            pruebas_reactivas=("pruebas_reactivas", "sum"),
            pct_reactivas_consejeria=("pct_reactivas_consejeria", "mean"),
            consultas_vih=("consultas_vih", "sum"),
            defunciones_vih=("defunciones_vih", "sum")
        )
    )

    anual["score_pruebas"] = minmax_serie(anual["pct_reactivas_consejeria"])
    anual["score_consultas"] = minmax_serie(anual["consultas_vih"])
    anual["score_defunciones"] = minmax_serie(anual["defunciones_vih"])

    anual["discrepancia_max_min"] = (
        anual[["score_pruebas", "score_consultas", "score_defunciones"]].max(axis=1)
        - anual[["score_pruebas", "score_consultas", "score_defunciones"]].min(axis=1)
    )
    anual["discrepancia_promedio"] = (
        (anual["score_pruebas"] - anual["score_consultas"]).abs()
        + (anual["score_pruebas"] - anual["score_defunciones"]).abs()
        + (anual["score_consultas"] - anual["score_defunciones"]).abs()
    ) / 3.0

    anual = anual.sort_values(["discrepancia_promedio", "discrepancia_max_min"], ascending=False).reset_index(drop=True)
    return anual

def responder_pregunta_19() -> pd.DataFrame:
    G = cargar_grafo()
    df = construir_tabla_metricas(G)

    df["delta_consultas"] = df["consultas_vih"].diff()
    df["delta_pruebas"] = df["pruebas_reactivas"].diff()
    df["delta_cd4_bajo"] = df["casos_cd4_bajo"].diff()
    df["delta_defunciones"] = df["defunciones_vih"].diff()

    df["caida_consultas_flag"] = (df["delta_consultas"] < 0).astype(int)
    df["caida_pruebas_flag"] = (df["delta_pruebas"] < 0).astype(int)
    df["persistencia_cd4_bajo_flag"] = (df["delta_cd4_bajo"] >= 0).astype(int)
    df["persistencia_defunciones_flag"] = (df["delta_defunciones"] >= 0).astype(int)

    df["score_desacople"] = (
        df["caida_consultas_flag"]
        + df["caida_pruebas_flag"]
        + df["persistencia_cd4_bajo_flag"]
        + df["persistencia_defunciones_flag"]
    )

    def clasificar(score):
        if pd.isna(score):
            return "SIN_REFERENCIA_PREVIA"
        if score >= 4:
            return "DESACOPLE_MUY_ALTO"
        if score == 3:
            return "DESACOPLE_ALTO"
        if score == 2:
            return "DESACOPLE_POSIBLE"
        return "SIN_DESACOPLE_CLARO"

    df["clasificacion_desacople"] = df["score_desacople"].apply(clasificar)

    columnas = [
        "anio", "mes", "periodo",
        "consultas_vih", "pruebas_reactivas", "casos_cd4_bajo", "defunciones_vih",
        "delta_consultas", "delta_pruebas", "delta_cd4_bajo", "delta_defunciones",
        "score_desacople", "clasificacion_desacople"
    ]
    return df[columnas]

def ejecutar_pregunta_grafo(numero_pregunta: int):
    if numero_pregunta == 2:
        return responder_pregunta_2()
    elif numero_pregunta == 7:
        return responder_pregunta_7()
    elif numero_pregunta == 8:
        return responder_pregunta_8()
    elif numero_pregunta == 10:
        return responder_pregunta_10()
    elif numero_pregunta == 19:
        return responder_pregunta_19()
    else:
        raise ValueError("Pregunta no registrada para backend grafo.")

# =========================================================
# SUBGRAFOS Y PLOTEO
# =========================================================

def construir_subgrafo_desde_resultado(G, resultado: pd.DataFrame):
    nodos_objetivo = set()

    fuentes_fijas = {"HGM", "VIH_RED", "DEFUNCIONES", "PRUEBAS"}
    periodos_fijos = {"PREPANDEMIA", "PANDEMIA", "POSTPANDEMIA", "FUERA_DE_RANGO"}

    for fuente in fuentes_fijas:
        if fuente in G.nodes:
            nodos_objetivo.add(fuente)

    for periodo in periodos_fijos:
        if periodo in G.nodes:
            nodos_objetivo.add(periodo)

    if "anio" in resultado.columns and "mes" in resultado.columns:
        for _, fila in resultado.iterrows():
            if pd.notna(fila["anio"]) and pd.notna(fila["mes"]):
                nodo_mes = f"M_{int(fila['anio'])}_{int(fila['mes']):02d}"
                if nodo_mes in G.nodes:
                    nodos_objetivo.add(nodo_mes)
                    for vecino in G.neighbors(nodo_mes):
                        nodos_objetivo.add(vecino)

    elif "anio" in resultado.columns:
        anios = resultado["anio"].dropna().astype(int).unique().tolist()

        for nodo, attrs in G.nodes(data=True):
            if attrs.get("tipo") == "mes" and attrs.get("anio") in anios:
                nodos_objetivo.add(nodo)
                for vecino in G.neighbors(nodo):
                    nodos_objetivo.add(vecino)

    return G.subgraph(nodos_objetivo).copy()

def obtener_color_nodo(tipo):
    if tipo == "fuente":
        return "lightblue"
    elif tipo == "periodo":
        return "lightgreen"
    elif tipo == "mes":
        return "lightcoral"
    return "lightgray"

def plotear_subgrafo(subG, numero_pregunta: int):
    plt.figure(figsize=(14, 9))

    colores_nodos = [
        obtener_color_nodo(attrs.get("tipo"))
        for _, attrs in subG.nodes(data=True)
    ]

    pos = nx.kamada_kawai_layout(subG)

    nx.draw_networkx_nodes(
        subG,
        pos,
        node_color=colores_nodos,
        node_size=900
    )

    nx.draw_networkx_edges(
        subG,
        pos,
        width=1.2,
        alpha=0.7
    )

    labels_filtradas = {}
    for nodo, attrs in subG.nodes(data=True):
        if attrs.get("tipo") in ["fuente", "periodo"]:
            labels_filtradas[nodo] = nodo
        elif attrs.get("tipo") == "mes":
            labels_filtradas[nodo] = ""

    nx.draw_networkx_labels(
        subG,
        pos,
        labels=labels_filtradas,
        font_size=9
    )

    plt.title(f"Subgrafo de la pregunta {numero_pregunta}")
    plt.axis("off")
    plt.tight_layout()

    archivo_salida = RESULTADOS_IMG_DIR / f"grafo_pregunta_{numero_pregunta}.png"
    plt.savefig(archivo_salida, dpi=300, bbox_inches="tight")
    plt.show()

    return archivo_salida

# =========================================================
# GUARDADO Y MENU
# =========================================================

def guardar_resultado_csv(resultado: pd.DataFrame, numero_pregunta: int) -> Path:
    ruta_salida = RESULTADOS_CSV_DIR / f"resultado_pregunta_{numero_pregunta}_grafo.csv"
    resultado.to_csv(ruta_salida, index=False, encoding="utf-8-sig")
    return ruta_salida

def mostrar_menu():
    print("##################################################")
    print("CONSULTAS GRAFO - AVANCE 5")
    print("##################################################\n")
    print("Preguntas disponibles:\n")
    for numero, texto in PREGUNTAS_GRAFO.items():
        print(f"{numero}: {texto}")
    print()

# =========================================================
# MAIN
# =========================================================

def main():
    mostrar_menu()
    numero_pregunta = int(input("Selecciona el numero de pregunta grafo: ").strip())

    resultado = ejecutar_pregunta_grafo(numero_pregunta)

    print("\nPrimeros 20 registros:\n")
    print(resultado.head(20))
    print("\nFilas devueltas:", len(resultado))

    ruta_csv = guardar_resultado_csv(resultado, numero_pregunta)
    print("Archivo CSV guardado en:", ruta_csv)

    G = cargar_grafo()
    subG = construir_subgrafo_desde_resultado(G, resultado)
    print("Nodos del subgrafo:", subG.number_of_nodes())
    print("Aristas del subgrafo:", subG.number_of_edges())

    ruta_img = plotear_subgrafo(subG, numero_pregunta)
    print("Imagen guardada en:", ruta_img)

if __name__ == "__main__":
    main()
