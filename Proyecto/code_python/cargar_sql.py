from pathlib import Path
import os

import psycopg2

from code_python.config import DB_CONFIG, RUTA_DATOS


def cargar_a_sql():
    conn = psycopg2.connect(**DB_CONFIG)

    cur = conn.cursor()

    ruta_base = RUTA_DATOS

    cargas = [
        (
            "consultas_HGM_cdmx_2019_2023_limpio_sin_duplicados_transformado.csv",
            "consultas_hgm"
        ),
        (
            "vih_red_completa_cdmx_2019_2023_limpio_sin_duplicados_transformado.csv",
            "vih_red"
        ),
        (
            "defunciones_registradas_cdmx_2019_2023_limpio_sin_duplicados_transformado.csv",
            "defunciones"
        )
    ]

    for archivo, tabla in cargas:
        ruta_csv = ruta_base / archivo

        cur.execute(f"TRUNCATE TABLE {tabla};")

        with open(ruta_csv, "r", encoding="utf-8-sig") as f:
            cur.copy_expert(
                f"""
                COPY {tabla}
                FROM STDIN
                WITH CSV HEADER DELIMITER ','
                """,
                f
            )

        print(f"Tabla cargada: {tabla} <- {archivo}")

    conn.commit()
    cur.close()
    conn.close()

    return ()
