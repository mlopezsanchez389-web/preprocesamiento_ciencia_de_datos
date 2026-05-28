from herramientas.deduplicador import ejecutar_deduplicacion
from pathlib import Path

def deduplicar_defunciones():
      
    ruta_proyecto = Path(__file__).resolve().parents[1]

    
    archivo = "defunciones_registradas_cdmx_2019_2023_limpio.csv"
    ruta = "Bases de datos"
    ruta = ruta_proyecto / ruta

    
    ejecutar_deduplicacion(
        archivo=ruta/archivo,
        encoding_archivo="utf-8",
        sep_archivo=",",
        variable_id="ID_REGISTRO_DEF",
        columnas_blocking=["FECHA_ANIO_MES", "EDAD", "MUN_OCURR"],
        umbral=4,
        comparaciones=[
            {"columna": "CAUSA_DEF", "tipo": "exact", "label": "causa_ok"},
            {"columna": "SEXO", "tipo": "exact", "label": "sexo_ok"},
            {"columna": "FECHA_OCURR", "tipo": "date", "label": "fecha_ocurr_ok", "margen_dias": 2},
            {"columna": "FECHA_NACIM", "tipo": "date", "label": "fecha_nacim_ok"},
        ]
    )
    return ()