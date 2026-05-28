from pathlib import Path
import pickle

import networkx as nx
import pandas as pd
import psycopg2


def crear_grafo_metricas_mensuales():
    conn = psycopg2.connect(
        dbname="proyecto_preprocesamiento_CD_VIH",
        user="postgres",
        password="deswa123",
        host="localhost",
        port="5432"
    )

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

    ruta_salida = Path("salidas_grafo")
    ruta_salida.mkdir(exist_ok=True)

    ruta_pickle = ruta_salida / "grafo_metricas_mensuales.pkl"
    ruta_csv_deltas = ruta_salida / "deltas_mensuales.csv"
    ruta_csv_nodos = ruta_salida / "nodos_mensuales.csv"

    with open(ruta_pickle, "wb") as f:
        pickle.dump(G, f)

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

    print("\nGrafo mensual creado correctamente.")
    print(f"Nodos: {G.number_of_nodes()}")
    print(f"Aristas: {G.number_of_edges()}")
    print(f"Archivo pickle: {ruta_pickle}")
    print(f"CSV de nodos mensuales: {ruta_csv_nodos}")
    print(f"CSV de deltas mensuales: {ruta_csv_deltas}")
    