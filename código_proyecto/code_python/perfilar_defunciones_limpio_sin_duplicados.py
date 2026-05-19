from perfilador import ejecutar_perfilado

ejecutar_perfilado(
    archivo="Bases de datos/fusion_defunciones_registradas_cdmx_2019_2023_limpio_sin_duplicados.csv",
    encoding_archivo="utf-8",
    separador_archivo=",",
    histogramas_a_generar=["EDAD", "ANIO_OCUR", "MES_OCURR"],
    columnas_numericas_boxplot=["EDAD", "ANIO_OCUR", "MES_OCURR"],
    variable_A="ANIO_OCUR",
    variable_B="SEXO",
    variable_C="VIH_FLAG",
    funcion_agregada="sum"
)
