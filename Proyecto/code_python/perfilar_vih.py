# %%
# %%
from code_python.herramientas.perfilador import ejecutar_perfilado


from pathlib import Path


ruta_proyecto = Path(__file__).resolve().parents[1]


archivo = "vih_red_completa_cdmx_2019_2023.csv"
ruta = "Bases de datos"
ruta = ruta_proyecto / ruta

ejecutar_perfilado(
    archivo= ruta/archivo,
    encoding_archivo="utf-8",
    separador_archivo=",",
    histogramas_a_generar=["edad", "cd4_a", "cv"],
    columnas_numericas_boxplot=["edad", "cd4_a", "cv"],
    columnas_categoricas=["sexo"],
    variable_A="sexo",
    variable_B="edad_rango",
    variable_C="cd4_a",
    funcion_agregada="count"
)

