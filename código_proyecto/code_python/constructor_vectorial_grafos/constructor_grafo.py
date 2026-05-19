import pandas as pd
import psycopg2
import networkx as nx
import pickle
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATOS_DIR = BASE_DIR / "datos" / "grafo"
DATOS_DIR.mkdir(parents=True, exist_ok=True)

ARCHIVO_GRAFO = DATOS_DIR / "grafo_metricas_mensuales.gpickle"


HOST = "localhost"
PORT = "5432"
DBNAME = "proyecto_preprocesamiento_CD_VIH"
USER = "postgres"
PASSWORD = "deswa123"


def obtener_conexion():
    return psycopg2.connect(
        host=HOST,
        port=PORT,
        dbname=DBNAME,
        user=USER,
        password=PASSWORD
    )

def cargar_metricas_mensuales() -> pd.DataFrame:
    consulta = "SELECT * FROM vw_metricas_mensuales_integradas ORDER BY fecha_orden_mes;"
    conn = obtener_conexion()
    try:
        df = pd.read_sql_query(consulta, conn)
    finally:
        conn.close()
    return df

def construir_grafo_metricas(df: pd.DataFrame) -> nx.Graph:
    G = nx.Graph()

    fuentes = ["HGM", "VIH_RED", "DEFUNCIONES", "PRUEBAS"]

    for fuente in fuentes:
        G.add_node(fuente, tipo="fuente")

    periodos = sorted(df["periodo"].dropna().unique().tolist())
    for periodo in periodos:
        G.add_node(periodo, tipo="periodo")

    for _, fila in df.iterrows():
        nodo_mes = f"M_{int(fila['anio'])}_{int(fila['mes']):02d}"

        G.add_node(
            nodo_mes,
            tipo="mes",
            fecha_orden_mes=int(fila["fecha_orden_mes"]),
            anio=int(fila["anio"]),
            mes=int(fila["mes"])
        )

        G.add_edge(nodo_mes, fila["periodo"], tipo="pertenece_a")

        G.add_edge(
            nodo_mes, "HGM",
            tipo="tiene_metricas",
            consultas_vih=int(fila["consultas_vih"]),
            consultas_vih_primera_vez=int(fila["consultas_vih_primera_vez"]),
            consultas_vih_subsecuente=int(fila["consultas_vih_subsecuente"])
        )

        G.add_edge(
            nodo_mes, "VIH_RED",
            tipo="tiene_metricas",
            muestras_total=int(fila["muestras_total"]),
            cd4_promedio=None if pd.isna(fila["cd4_promedio"]) else float(fila["cd4_promedio"]),
            casos_cd4_bajo=int(fila["casos_cd4_bajo"]),
            proporcion_cd4_bajo=None if pd.isna(fila["proporcion_cd4_bajo"]) else float(fila["proporcion_cd4_bajo"])
        )

        G.add_edge(
            nodo_mes, "DEFUNCIONES",
            tipo="tiene_metricas",
            total_defunciones=int(fila["total_defunciones"]),
            defunciones_vih=int(fila["defunciones_vih"])
        )

        G.add_edge(
            nodo_mes, "PRUEBAS",
            tipo="tiene_metricas",
            pruebas_reactivas=int(fila["pruebas_reactivas"]),
            pct_reactivas_consejeria=None if pd.isna(fila["pct_reactivas_consejeria"]) else float(fila["pct_reactivas_consejeria"]),
            pct_reactivas_otros_programas=None if pd.isna(fila["pct_reactivas_otros_programas"]) else float(fila["pct_reactivas_otros_programas"])
        )

    return G

def main():
    df = cargar_metricas_mensuales()
    G = construir_grafo_metricas(df)

    with open(ARCHIVO_GRAFO, "wb") as f:
        pickle.dump(G, f)

    print("Grafo generado correctamente")
    print("Nodos:", G.number_of_nodes())
    print("Aristas:", G.number_of_edges())

    ejemplo_mes = "M_2020_03"
    if ejemplo_mes in G.nodes:
        print("\nNodo ejemplo:", ejemplo_mes)
        print(G.nodes[ejemplo_mes])

        print("\nArista ejemplo con HGM:")
        print(G.get_edge_data(ejemplo_mes, "HGM"))

if __name__ == "__main__":
    main()