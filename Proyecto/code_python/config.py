from pathlib import Path
import os


RUTA_PROYECTO = Path(__file__).resolve().parents[1]
RUTA_DATOS = RUTA_PROYECTO / "Bases de datos"
RUTA_SALIDAS = RUTA_PROYECTO / "salidas"

SALIDA_PERFILADO = RUTA_SALIDAS / "perfilado"
SALIDA_ANALISIS = RUTA_SALIDAS / "analisis"
SALIDA_GRAFO = RUTA_SALIDAS / "grafo"
SALIDA_VECTORIAL = RUTA_SALIDAS / "vectorial"

RUTA_MODELO = RUTA_PROYECTO / "modelos" / "Llama-3.2-3B-Instruct-Q4_K_M.gguf"

DB_CONFIG = {
    "dbname": os.getenv("PGDATABASE", "proyecto_preprocesamiento_CD_VIH"),
    "user": os.getenv("PGUSER", "postgres"),
    "password": os.getenv("PGPASSWORD", "deswa123"),
    "host": os.getenv("PGHOST", "localhost"),
    "port": os.getenv("PGPORT", "5432"),
}
