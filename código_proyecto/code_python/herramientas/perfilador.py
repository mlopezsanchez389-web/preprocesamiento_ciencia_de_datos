# Práctica / apoyo para perfilado de bases CSV
# Nombre: Miguel Angel López Sánchez
# Perfilado general reutilizable para bases del proyecto

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import recordlinkage

pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option("display.expand_frame_repr", False)



################## FUNCION CARGAR ARCHIVO CSV ##################
# Esta función lee cualquier archivo CSV y devuelve el dataframe.

def cargar_datos(archivo_csv: str, encoding: str, sep: str) -> pd.DataFrame:

    df = pd.read_csv(archivo_csv, encoding=encoding, sep=sep, low_memory=False)
    return df

################## PASO 1 - ESTRUCTURA BASICA ##################
# Se imprime el número de registros y el número de columnas.

def mostrar_estructura(df: pd.DataFrame) -> None:

    print("##################################################")
    print("PASO 1 - ESTRUCTURA BASICA")
    print("##################################################\n")

    print("Número de filas:", df.shape[0])
    print("Número de columnas:", df.shape[1])
    print("\n")

################## PASO 2 - DENSIDAD, COMPLETITUD Y CARDINALIDAD ##################
# Se calcula densidad, completitud, nulos y cardinalidad por columna.

def generar_perfil_columnas(df: pd.DataFrame) -> pd.DataFrame:

    print("##################################################")
    print("PASO 2 - DENSIDAD, COMPLETITUD Y CARDINALIDAD")
    print("##################################################\n")

    total_registros = len(df)

    resumen_columnas = []

    for columna in df.columns:
        no_nulos = df[columna].notna().sum()
        nulos = df[columna].isna().sum()
        densidad = (no_nulos / total_registros) * 100
        completitud = (no_nulos / total_registros) * 100
        cardinalidad = df[columna].nunique(dropna=True)

        resumen_columnas.append({
            "columna": columna,
            "no_nulos": no_nulos,
            "nulos": nulos,
            "densidad_%": round(densidad, 2),
            "completitud_%": round(completitud, 2),
            "cardinalidad": cardinalidad
        })

    df_resumen = pd.DataFrame(resumen_columnas)

    print(df_resumen)
    print("\n")

    return df_resumen

################## PASO 3 - GRAFICAR HISTOGRAMAS ##################
# Se generan histogramas solo de las columnas seleccionadas.

def imprimir_histogramas_como_tabla(df: pd.DataFrame, histogramas_a_generar: list, bins: int) -> None:

    print("##################################################")
    print("PASO 3 - HISTOGRAMAS COMO TABLA")
    print("##################################################\n")

    for columna in histogramas_a_generar:
        serie = pd.to_numeric(df[columna], errors="coerce").dropna()

        frecuencias, bordes = np.histogram(serie, bins=bins, range=(0, serie.max()))

        tabla_hist = pd.DataFrame({
            "limite_inferior": bordes[:-1],
            "limite_superior": bordes[1:],
            "frecuencia": frecuencias
        })

        print(f"Histograma en tabla para: {columna}")
        print(tabla_hist)
        print("\n")

def graficar_histogramas(df: pd.DataFrame, histogramas_a_generar: list) -> None:

    print("##################################################")
    print("PASO 3 - HISTOGRAMAS")
    print("##################################################\n")

    for columna in histogramas_a_generar:
        serie = pd.to_numeric(df[columna], errors="coerce").dropna()

        plt.figure(figsize=(8, 5))
        plt.hist(serie, bins=15, edgecolor="black")
        plt.title(f"Histograma de {columna}")
        plt.xlabel(columna)
        plt.ylabel("Frecuencia")
        plt.tight_layout()
        plt.show()

################## PASO 4 - CAJA Y BIGOTES + RESUMEN NUMERICO ##################
# Se generan boxplots de columnas numéricas y se imprimen Q1, Q2, Q3, media,
# desviación estándar, mediana y moda.

def generar_boxplot_y_resumen(df: pd.DataFrame, columnas_numericas: list) -> pd.DataFrame:

    print("##################################################")
    print("PASO 4 - CAJA Y BIGOTES + RESUMEN NUMERICO")
    print("##################################################\n")

    resumen = []

    for columna in columnas_numericas:
        serie = pd.to_numeric(df[columna], errors="coerce").dropna()
        minimo=min(serie)
        maximo=max(serie)
        q1 = serie.quantile(0.25)
        q2 = serie.quantile(0.50)
        q3 = serie.quantile(0.75)
        media = serie.mean()
        desv_std = serie.std()
        mediana = serie.median()
        moda = serie.mode().iloc[0]
        

        resumen.append({
            "columna": columna,
            "Q1": round(q1, 4),
            "Q2": round(q2, 4),
            "Q3": round(q3, 4),
            "media": round(media, 4),
            "desv_std": round(desv_std, 4),
            "mediana": round(mediana, 4),
            "moda": round(moda, 4),
            "Valor mín: ": round(minimo, 4),
            "Valor max: ": round(maximo, 4)
        })

        plt.figure(figsize=(7, 4))
        plt.boxplot(serie, vert=True, patch_artist=False)
        plt.title(f"Caja y bigotes de {columna}")
        plt.ylabel(columna)
        plt.tight_layout()
        plt.show()

    df_resumen = pd.DataFrame(resumen)
    print(df_resumen)
    print("\n")

    return df_resumen

################## PASO 5 - DISTRIBUCION APILADA ##################
# Se construye una gráfica de columnas apiladas tipo tabla dinámica:
# A = filas/eje, B = columnas/leyenda, C = valores.

def graficar_distribucion_apilada(
    df: pd.DataFrame,
    variable_A: str,
    variable_B: str,
    variable_C: str,
    funcion_agregada: str
) -> None:

    print("##################################################")
    print("PASO 5 - DISTRIBUCION APILADA")
    print("##################################################\n")

    tmp = df[[variable_A, variable_B, variable_C]].copy()

    tabla = tmp.pivot_table(
        index=variable_A,
        columns=variable_B,
        values=variable_C,
        aggfunc=funcion_agregada,
        fill_value=0
    )

    tabla.plot(kind="bar", stacked=True, figsize=(10, 6))
    plt.title(f"Distribución apilada: {variable_A} vs {variable_B} usando {variable_C}")
    plt.xlabel(variable_A)
    plt.ylabel("Conteo")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', ncol=3)
    plt.show()

def ejecutar_perfilado(
    archivo,
    encoding_archivo,
    separador_archivo,
    histogramas_a_generar,
    columnas_numericas_boxplot,
    variable_A,
    variable_B,
    variable_C,
    funcion_agregada
):
    df = cargar_datos(archivo, encoding=encoding_archivo, sep=separador_archivo)

    print("##################################################")
    print("ARCHIVO ANALIZADO:", archivo)
    print("##################################################\n")

    mostrar_estructura(df)
    perfil = generar_perfil_columnas(df)
    graficar_histogramas(df, histogramas_a_generar=histogramas_a_generar)
    resumen_boxplot = generar_boxplot_y_resumen(df, columnas_numericas=columnas_numericas_boxplot)
    graficar_distribucion_apilada(
        df,
        variable_A=variable_A,
        variable_B=variable_B,
        variable_C=variable_C,
        funcion_agregada=funcion_agregada
    )