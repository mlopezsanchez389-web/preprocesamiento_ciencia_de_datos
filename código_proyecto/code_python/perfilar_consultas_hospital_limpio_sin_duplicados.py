from pathlib import Path

ruta_proyecto = Path(__file__).resolve().parents[1]


archivo = "consultas_HGM_cdmx_2019_2023_limpio_sin_duplicados.csv"
ruta = "Bases de datos"
ruta = ruta_proyecto / ruta

from herramientas.perfilador import ejecutar_perfilado


ejecutar_perfilado(
    archivo=ruta/archivo,
    encoding_archivo="utf-8",
    separador_archivo=",",
    histogramas_a_generar=["EDAD"],
    columnas_numericas_boxplot=["EDAD"],
    variable_A="SEXO",
    variable_B="EDAD_RANGO",
    variable_C="VIH_FLAG",
    funcion_agregada="sum"
)
