from pathlib import Path
import pandas as pd
import psycopg2

# =========================================================
# CONFIGURACION GENERAL
# =========================================================

HOST = "localhost"
PORT = "5432"
DBNAME = "proyecto_preprocesamiento_CD_VIH"
USER = "postgres"
PASSWORD = "deswa123"

BASE_DIR = Path(__file__).resolve().parent
RESULTADOS_DIR = BASE_DIR / "resultados" / "sql"
RESULTADOS_DIR.mkdir(parents=True, exist_ok=True)

# =========================================================
# RUTEO DE PREGUNTAS SQL
# =========================================================

PREGUNTAS_SQL = {
    1: "Tendencia de consultas VIH vs defunciones VIH",
    3: "Pruebas reactivas vs consultas y defunciones",
    4: "Diferencias por sexo",
    5: "Diferencias por edad",
    6: "Prepandemia, pandemia y postpandemia",
    9: "Patrón temporal de CD4 bajo",
    12: "Menos consultas y menos pruebas vs CD4 bajo",
    13: "Perfiles sexo-edad con mayor severidad",
    14: "Pruebas reactivas vs demanda clínica",
    17: "Sexo-edad y detección tardía",
    18: "Pruebas reactivas vs defunciones al año siguiente"
}

RUTEO_SQL = {
    1: "vw_respuesta_sql_1",
    3: "vw_respuesta_sql_3",
    4: "vw_respuesta_sql_4",
    5: "vw_respuesta_sql_5",
    6: "vw_respuesta_sql_6",
    9: "vw_respuesta_sql_9",
    12: "vw_respuesta_sql_12",
    13: "vw_respuesta_sql_13",
    14: "vw_respuesta_sql_14",
    17: "vw_respuesta_sql_17",
    18: "vw_respuesta_sql_18"
}

# =========================================================
# FUNCIONES
# =========================================================

def obtener_conexion():
    return psycopg2.connect(
        host=HOST,
        port=PORT,
        dbname=DBNAME,
        user=USER,
        password=PASSWORD
    )

def ejecutar_pregunta_sql(numero_pregunta: int) -> pd.DataFrame:
    nombre_vista = RUTEO_SQL[numero_pregunta]
    consulta = f"SELECT * FROM {nombre_vista};"

    with obtener_conexion() as conn:
        df = pd.read_sql_query(consulta, conn)

    return df

def guardar_resultado(resultado: pd.DataFrame, numero_pregunta: int) -> Path:
    ruta_salida = RESULTADOS_DIR / f"resultado_pregunta_{numero_pregunta}_sql.csv"
    resultado.to_csv(ruta_salida, index=False, encoding="utf-8-sig")
    return ruta_salida

def mostrar_menu():
    print("##################################################")
    print("CONSULTAS SQL - AVANCE 5")
    print("##################################################\n")
    print("Preguntas disponibles:\n")

    for numero, texto in PREGUNTAS_SQL.items():
        vista = RUTEO_SQL[numero]
        print(f"{numero}: {texto} [{vista}]")

    print()

# =========================================================
# MAIN
# =========================================================

def main():
    mostrar_menu()
    numero_pregunta = int(input("Selecciona el número de pregunta SQL: ").strip())

    resultado = ejecutar_pregunta_sql(numero_pregunta)

    print("\nPrimeros 20 registros:\n")
    print(resultado.head(20))
    print("\nFilas devueltas:", len(resultado))

    ruta_salida = guardar_resultado(resultado, numero_pregunta)
    print("Archivo guardado en:", ruta_salida)

if __name__ == "__main__":
    main()
