from code_python.herramientas.perfilador import ejecutar_perfilado


ejecutar_perfilado(
    archivo="Bases de datos/defunciones_registradas_cdmx_2019_2023_limpio_sin_duplicados.csv",
    encoding_archivo="utf-8",
    separador_archivo=",",
    histogramas_a_generar=["EDAD"],
    columnas_numericas_boxplot=["EDAD"],
    columnas_categoricas=["SEXO", "VIH_FLAG"],
    variable_A="ANIO_OCUR",
    variable_B="SEXO",
    variable_C="VIH_FLAG",
    funcion_agregada="sum"
)
