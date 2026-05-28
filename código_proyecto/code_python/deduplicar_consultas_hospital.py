from herramientas.deduplicador import ejecutar_deduplicacion
from pathlib import Path

def deduplicar_consultas_hospital():
    
    ruta_proyecto = Path(__file__).resolve().parents[1]

    
    archivo = "consultas_HGM_cdmx_2019_2023_limpio.csv"
    ruta = "Bases de datos"
    ruta = ruta_proyecto / ruta

    ejecutar_deduplicacion(
        archivo=ruta/archivo,
        encoding_archivo="utf-8",
        sep_archivo=",",
        variable_id="ID_REGISTRO",
        columnas_blocking=["FECHA_ANIO_MES", "SEXO", "EDAD_RANGO", "ESPECIALIDAD"],
        umbral=5,
        comparaciones=[
            {"columna": "TIPO_CONSULTA", "tipo": "exact", "label": "tipo_consulta_ok"},
            {"columna": "SEXO", "tipo": "exact", "label": "sexo_ok"},
            {"columna": "EDAD", "tipo": "exact", "label": "edad_ok"},
            {"columna": "CODIGO", "tipo": "exact", "label": "codigo_ok"},
            {"columna": "FECHA", "tipo": "date", "label": "fecha_ok", "margen_dias": 0},
        ]
    )
    return ()