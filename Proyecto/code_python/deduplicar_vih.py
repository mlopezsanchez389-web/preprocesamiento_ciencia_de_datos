from code_python.herramientas.deduplicador import ejecutar_deduplicacion
from pathlib import Path

def deduplicar_vih():
      
    ruta_proyecto = Path(__file__).resolve().parents[1]

    
    archivo = "vih_red_completa_cdmx_2019_2023_limpio.csv"
    ruta = "Bases de datos"
    ruta = ruta_proyecto / ruta

    
    ejecutar_deduplicacion(
        archivo=ruta/archivo,
        encoding_archivo="utf-8",
        sep_archivo=",",
        variable_id="ID_MUESTRA",
        columnas_blocking=["FECHA_ANIO_MES", "EDAD_RANGO", "MUNICIPIO"],
        umbral=4.5,
        comparaciones=[
            {"columna": "SEXO", "tipo": "exact", "label": "sexo_ok"},
            {"columna": "GENERO", "tipo": "exact", "label": "genero_ok"},
            {"columna": "EDAD", "tipo": "exact", "label": "edad_ok"},
            {"columna": "CD4_A", "tipo": "numeric", "label": "cd4_ok", "metodo": "linear", "offset": 10, "scale": 40},
            {"columna": "FECHA_TOMA", "tipo": "date", "label": "fecha_toma_ok", "margen_dias": 2},
        ]
    )
    return ()
    

