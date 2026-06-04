from code_python.herramientas.perfilador import ejecutar_perfilado


ejecutar_perfilado(
    archivo="Bases de datos/vih_red_completa_cdmx_2019_2023_limpio_sin_duplicados.csv",
    encoding_archivo="utf-8",
    separador_archivo=",",
    histogramas_a_generar=["EDAD", "CD4_A", "CV"],
    columnas_numericas_boxplot=["EDAD", "CD4_A", "CV"],
    columnas_categoricas=["SEXO", "VIH_TARDIO_FLAG"],
    variable_A="SEXO",
    variable_B="EDAD_RANGO",
    variable_C="VIH_TARDIO_FLAG",
    funcion_agregada="sum"
)
