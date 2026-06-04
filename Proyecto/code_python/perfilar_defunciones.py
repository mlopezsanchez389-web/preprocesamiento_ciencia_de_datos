from code_python.herramientas.perfilador import ejecutar_perfilado
from pathlib import Path


ruta_proyecto = Path(__file__).resolve().parents[1]


archivo = "defunciones_registradas_cdmx_2019_2023.csv"
ruta = "Bases de datos"
ruta = ruta_proyecto / ruta

ejecutar_perfilado(
    archivo=ruta/archivo,
    encoding_archivo="utf-8",
    separador_archivo=",",
    histogramas_a_generar=["EDAD"],
    columnas_numericas_boxplot=["EDAD"],
    columnas_categoricas=["SEXO"],
    variable_A="ANIO_OCUR",
    variable_B="SEXO",
    variable_C="CAUSA_DEF",
    funcion_agregada="count"
)

