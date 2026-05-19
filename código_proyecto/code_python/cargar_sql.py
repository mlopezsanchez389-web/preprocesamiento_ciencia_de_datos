import psycopg2
from pathlib import Path

def cargar_a_sql ():
    
    conn = psycopg2.connect(
        dbname="proyecto_preprocesamiento_CD_VIH",
        user="postgres",
        password="deswa123",
        host="localhost",
        port="5432"
    )
    
    cur = conn.cursor()
    
    ruta_proyecto = Path(__file__).resolve().parents[1]
    ruta_base = ruta_proyecto / "Bases de datos"
    
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
        print(f"La tabla {tabla} ha sido actualizada con éxito con los datos de {archivo}\n")
        
        
    conn.commit()
    
    cur.close()
    conn.close()
    
    return ()