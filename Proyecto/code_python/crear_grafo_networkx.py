from pathlib import Path
import json
import os
import pickle

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd
import psycopg2

from code_python.config import DB_CONFIG, SALIDA_GRAFO


def _valor_json(valor):
    if pd.isna(valor):
        return None
    if hasattr(valor, "item"):
        return valor.item()
    return valor


def _exportar_grafo_json(G, ruta_json):
    datos = {
        "tipo": "grafo_metricas_mensuales",
        "nodos": [
            {
                "id": nodo,
                "atributos": {
                    clave: _valor_json(valor)
                    for clave, valor in atributos.items()
                }
            }
            for nodo, atributos in G.nodes(data=True)
        ],
        "aristas": [
            {
                "origen": origen,
                "destino": destino,
                "atributos": {
                    clave: _valor_json(valor)
                    for clave, valor in atributos.items()
                }
            }
            for origen, destino, atributos in G.edges(data=True)
        ]
    }

    with open(ruta_json, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)


def _exportar_grafo_png(G, ruta_png):
    colores_tipo = {
        "mes": "#4C78A8",
        "periodo": "#F58518",
        "indicador": "#54A24B",
    }

    colores = [
        colores_tipo.get(G.nodes[nodo].get("tipo"), "#999999")
        for nodo in G.nodes
    ]
    tamanos = [
        420 if G.nodes[nodo].get("tipo") == "periodo"
        else 220 if G.nodes[nodo].get("tipo") == "indicador"
        else 95
        for nodo in G.nodes
    ]

    orden_periodos = {
        "PERIODO_PREPANDEMIA": 1,
        "PERIODO_PANDEMIA": 2,
        "PERIODO_POSTPANDEMIA": 3,
    }
    periodos = sorted(
        [n for n, d in G.nodes(data=True) if d.get("tipo") == "periodo"],
        key=lambda n: orden_periodos.get(n, 99)
    )
    meses = sorted(
        [n for n, d in G.nodes(data=True) if d.get("tipo") == "mes"],
        key=lambda n: G.nodes[n].get("fecha_orden_mes", 0)
    )
    indicadores = sorted([n for n, d in G.nodes(data=True) if d.get("tipo") == "indicador"])

    pos = {}

    for fila, nodos in [(2, periodos), (1, meses), (0, indicadores)]:
        if len(nodos) == 1:
            pos[nodos[0]] = (0, fila)
            continue

        for i, nodo in enumerate(nodos):
            x = -1 + (2 * i / max(len(nodos) - 1, 1))
            pos[nodo] = (x, fila)

    plt.figure(figsize=(24, 18))
    nx.draw_networkx_edges(
        G,
        pos,
        arrows=True,
        arrowstyle="-|>",
        arrowsize=8,
        width=0.45,
        alpha=0.22,
        edge_color="#555555"
    )
    nx.draw_networkx_nodes(
        G,
        pos,
        node_color=colores,
        node_size=tamanos,
        linewidths=0.35,
        edgecolors="#222222",
        alpha=0.92
    )
    nx.draw_networkx_labels(G, pos, font_size=5)

    plt.title("Grafo de periodos, meses e indicadores", fontsize=16)
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(ruta_png, dpi=220)
    plt.close()


def crear_grafo_metricas_mensuales():
    conn = psycopg2.connect(**DB_CONFIG)

    consulta = """
        SELECT
            fecha_orden_mes,
            anio,
            mes,

            total_consultas,
            consultas_vih,
            proporcion_consultas_vih,

            muestras_total,
            cd4_promedio,
            casos_cd4_bajo,
            proporcion_cd4_bajo,

            total_defunciones,
            defunciones_vih,
            proporcion_defunciones_vih,

            pruebas_reactivas,
            pct_reactivas_consejeria,
            pct_reactivas_otros_programas,

            periodo
        FROM vw_metricas_mensuales_integradas
        ORDER BY fecha_orden_mes;
    """

    df = pd.read_sql_query(consulta, conn)
    conn.close()

    metricas_nodo = [
        "total_consultas",
        "consultas_vih",
        "proporcion_consultas_vih",
        "muestras_total",
        "cd4_promedio",
        "casos_cd4_bajo",
        "proporcion_cd4_bajo",
        "total_defunciones",
        "defunciones_vih",
        "proporcion_defunciones_vih",
        "pruebas_reactivas",
        "pct_reactivas_consejeria",
        "pct_reactivas_otros_programas",
    ]

    metricas_delta = [
        "proporcion_consultas_vih",
        "proporcion_cd4_bajo",
        "proporcion_defunciones_vih",
    ]

    df_delta = df.copy()
    df_delta[metricas_delta] = df_delta[metricas_delta].ffill()

    G = nx.DiGraph()

    periodos = sorted(df["periodo"].dropna().unique())

    for periodo in periodos:
        G.add_node(
            f"PERIODO_{periodo}",
            tipo="periodo",
            periodo=periodo
        )

    for metrica in metricas_nodo:
        G.add_node(
            f"IND_{metrica}",
            tipo="indicador",
            indicador=metrica
        )

    registros_deltas = []

    nodos_mes = []

    for i, fila in df.iterrows():
        nodo_mes = f"MES_{int(fila['anio'])}_{int(fila['mes']):02d}"
        nodos_mes.append(nodo_mes)

        atributos_mes = {
            "tipo": "mes",
            "fecha_orden_mes": int(fila["fecha_orden_mes"]),
            "anio": int(fila["anio"]),
            "mes": int(fila["mes"]),
            "periodo": fila["periodo"],
        }

        for metrica in metricas_nodo:
            valor = fila[metrica]
            atributos_mes[metrica] = None if pd.isna(valor) else valor

        G.add_node(nodo_mes, **atributos_mes)

        if pd.notna(fila["periodo"]):
            G.add_edge(
                nodo_mes,
                f"PERIODO_{fila['periodo']}",
                tipo="PERTENECE_A_PERIODO"
            )

        for metrica in metricas_nodo:
            valor = fila[metrica]
            G.add_edge(
                nodo_mes,
                f"IND_{metrica}",
                tipo="TIENE_INDICADOR",
                valor=None if pd.isna(valor) else valor
            )

    for i in range(1, len(df_delta)):
        fila_anterior = df_delta.iloc[i - 1]
        fila_actual = df_delta.iloc[i]

        nodo_origen = f"MES_{int(fila_anterior['anio'])}_{int(fila_anterior['mes']):02d}"
        nodo_destino = f"MES_{int(fila_actual['anio'])}_{int(fila_actual['mes']):02d}"

        atributos_arista = {
            "tipo": "SIGUIENTE_MES",
            "fecha_orden_mes_origen": int(fila_anterior["fecha_orden_mes"]),
            "fecha_orden_mes_destino": int(fila_actual["fecha_orden_mes"]),
        }

        registro_delta = {
            "mes_origen": nodo_origen,
            "mes_destino": nodo_destino,
            "fecha_orden_mes_origen": int(fila_anterior["fecha_orden_mes"]),
            "fecha_orden_mes_destino": int(fila_actual["fecha_orden_mes"]),
            "anio_origen": int(fila_anterior["anio"]),
            "mes_origen_num": int(fila_anterior["mes"]),
            "anio_destino": int(fila_actual["anio"]),
            "mes_destino_num": int(fila_actual["mes"]),
            "periodo_origen": fila_anterior["periodo"],
            "periodo_destino": fila_actual["periodo"],
        }

        for metrica in metricas_delta:
            valor_anterior = fila_anterior[metrica]
            valor_actual = fila_actual[metrica]

            if pd.isna(valor_anterior) or pd.isna(valor_actual):
                delta = None
                pct_delta = None
                cambio = "sin_dato"
            else:
                delta = valor_actual - valor_anterior

                if valor_anterior == 0:
                    pct_delta = None
                else:
                    pct_delta = delta / abs(valor_anterior)

                if delta > 0:
                    cambio = "sube"
                elif delta < 0:
                    cambio = "baja"
                else:
                    cambio = "sin_cambio"

            atributos_arista[f"delta_{metrica}"] = delta
            atributos_arista[f"pct_delta_{metrica}"] = pct_delta
            atributos_arista[f"cambio_{metrica}"] = cambio

            registro_delta[f"valor_anterior_{metrica}"] = None if pd.isna(valor_anterior) else valor_anterior
            registro_delta[f"valor_actual_{metrica}"] = None if pd.isna(valor_actual) else valor_actual
            registro_delta[f"delta_{metrica}"] = delta
            registro_delta[f"pct_delta_{metrica}"] = pct_delta
            registro_delta[f"cambio_{metrica}"] = cambio

        G.add_edge(
            nodo_origen,
            nodo_destino,
            **atributos_arista
        )

        registros_deltas.append(registro_delta)

    ruta_salida = SALIDA_GRAFO
    ruta_salida.mkdir(exist_ok=True)

    ruta_pickle = ruta_salida / "grafo_metricas_mensuales.pkl"
    ruta_json = ruta_salida / "grafo_metricas_mensuales.json"
    ruta_png = ruta_salida / "grafo_metricas_mensuales.png"
    ruta_csv_deltas = ruta_salida / "deltas_mensuales.csv"
    ruta_csv_nodos = ruta_salida / "nodos_mensuales.csv"

    with open(ruta_pickle, "wb") as f:
        pickle.dump(G, f)

    _exportar_grafo_json(G, ruta_json)
    _exportar_grafo_png(G, ruta_png)

    pd.DataFrame(registros_deltas).to_csv(
        ruta_csv_deltas,
        index=False,
        encoding="utf-8-sig"
    )

    df.to_csv(
        ruta_csv_nodos,
        index=False,
        encoding="utf-8-sig"
    )

    print("Grafo mensual generado.")
    print(f"Nodos: {G.number_of_nodes()}")
    print(f"Aristas: {G.number_of_edges()}")
    print(f"Pickle: {ruta_pickle}")
    print(f"JSON: {ruta_json}")
    print(f"Imagen: {ruta_png}")
    print(f"Nodos mensuales: {ruta_csv_nodos}")
    print(f"Deltas mensuales: {ruta_csv_deltas}")
    
