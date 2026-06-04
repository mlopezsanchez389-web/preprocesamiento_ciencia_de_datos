from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from code_python.herramientas.reporte_consola import titulo, seccion, metrica, tabla
from code_python.config import SALIDA_PERFILADO


pd.set_option("display.max_rows", None)
pd.set_option("display.max_columns", None)
pd.set_option("display.expand_frame_repr", False)


def _nombre_archivo(texto):
    texto = str(texto).replace(" ", "_").replace("/", "_").replace("\\", "_")
    return "".join(c for c in texto if c.isalnum() or c in "._-")


def _prefijo_archivo(df):
    return _nombre_archivo(Path(df.attrs.get("archivo_origen", "datos")).stem)


def _carpeta_salida():
    carpeta = SALIDA_PERFILADO
    carpeta.mkdir(parents=True, exist_ok=True)
    return carpeta


def cargar_datos(archivo_csv, encoding, sep):
    return pd.read_csv(archivo_csv, encoding=encoding, sep=sep, low_memory=False)


def mostrar_estructura(df):
    seccion("Resumen de estructura")
    metrica("Filas", df.shape[0])
    metrica("Columnas", df.shape[1])


def generar_perfil_columnas(df):
    seccion("Densidad, completitud y cardinalidad")

    total_registros = len(df)
    resumen_columnas = []

    for columna in df.columns:
        no_nulos = df[columna].notna().sum()
        nulos = df[columna].isna().sum()
        completitud = (no_nulos / total_registros) * 100 if total_registros else 0
        cardinalidad = df[columna].nunique(dropna=True)

        resumen_columnas.append({
            "columna": columna,
            "no_nulos": no_nulos,
            "nulos": nulos,
            "densidad_%": round(completitud, 2),
            "completitud_%": round(completitud, 2),
            "cardinalidad": cardinalidad
        })

    df_resumen = pd.DataFrame(resumen_columnas)
    tabla("Resumen por columna", df_resumen, max_filas=50)
    tabla("Columnas con mas nulos", df_resumen[df_resumen["nulos"] > 0].sort_values("nulos", ascending=False), max_filas=10)
    tabla("Columnas con mayor cardinalidad", df_resumen.sort_values("cardinalidad", ascending=False), max_filas=10)
    return df_resumen


def graficar_histogramas(df, columnas, carpeta_salida):
    seccion("Histogramas numericos")

    for columna in columnas:
        if columna not in df.columns:
            print(f"Columna no encontrada para histograma: {columna}")
            continue

        serie = pd.to_numeric(df[columna], errors="coerce").dropna()
        if serie.empty:
            print(f"Sin datos numericos para histograma: {columna}")
            continue

        plt.figure(figsize=(8, 5))
        plt.hist(serie, bins=20, edgecolor="black", color="#4C78A8", label=f"n={len(serie)}")
        plt.title(f"Histograma de {columna}")
        plt.xlabel(columna)
        plt.ylabel("Frecuencia")
        plt.legend(title="Registros")
        plt.grid(axis="y", alpha=0.25)
        plt.tight_layout()

        ruta_png = carpeta_salida / f"{_prefijo_archivo(df)}_histograma_{_nombre_archivo(columna)}.png"
        plt.savefig(ruta_png, dpi=180)
        plt.close()
        print(f"Imagen guardada: {ruta_png}")


def generar_boxplot_y_resumen(df, columnas, carpeta_salida):
    seccion("Caja y bigotes + resumen numerico")
    resumen = []

    for columna in columnas:
        if columna not in df.columns:
            print(f"Columna no encontrada para boxplot: {columna}")
            continue

        serie = pd.to_numeric(df[columna], errors="coerce").dropna()
        if serie.empty:
            print(f"Sin datos numericos para boxplot: {columna}")
            continue

        moda = serie.mode()
        resumen.append({
            "columna": columna,
            "Q1": round(serie.quantile(0.25), 4),
            "Q2": round(serie.quantile(0.50), 4),
            "Q3": round(serie.quantile(0.75), 4),
            "media": round(serie.mean(), 4),
            "desv_std": round(serie.std(), 4),
            "mediana": round(serie.median(), 4),
            "moda": round(moda.iloc[0], 4) if not moda.empty else None,
            "valor_min": round(serie.min(), 4),
            "valor_max": round(serie.max(), 4)
        })

        plt.figure(figsize=(7, 4))
        plt.boxplot(serie, vert=True, patch_artist=True)
        plt.title(f"Boxplot de {columna}")
        plt.ylabel(columna)
        plt.grid(axis="y", alpha=0.25)
        plt.tight_layout()

        ruta_png = carpeta_salida / f"{_prefijo_archivo(df)}_boxplot_{_nombre_archivo(columna)}.png"
        plt.savefig(ruta_png, dpi=180)
        plt.close()
        print(f"Imagen guardada: {ruta_png}")

    df_resumen = pd.DataFrame(resumen)
    tabla("Resumen de variables numericas", df_resumen, max_filas=50)
    return df_resumen


def graficar_frecuencias_categoricas(df, columnas, carpeta_salida):
    seccion("Frecuencias categoricas")

    for columna in columnas:
        if columna not in df.columns:
            print(f"Columna no encontrada para frecuencias: {columna}")
            continue

        conteos = df[columna].fillna("SIN_DATO").astype(str).value_counts().head(20)
        if conteos.empty:
            print(f"Sin datos para frecuencias: {columna}")
            continue

        tabla_freq = conteos.rename_axis(columna).reset_index(name="frecuencia")
        tabla(f"Frecuencias de {columna}", tabla_freq, max_filas=20)

        plt.figure(figsize=(9, 5))
        ax = conteos.sort_values().plot(kind="barh", color="#54A24B")
        ax.set_title(f"Frecuencia de {columna}")
        ax.set_xlabel("Frecuencia")
        ax.set_ylabel(columna)
        ax.grid(axis="x", alpha=0.25)

        for contenedor in ax.containers:
            ax.bar_label(contenedor, label_type="edge", fontsize=8, padding=2)

        plt.tight_layout()
        ruta_png = carpeta_salida / f"{_prefijo_archivo(df)}_frecuencia_{_nombre_archivo(columna)}.png"
        plt.savefig(ruta_png, dpi=180)
        plt.close()
        print(f"Imagen guardada: {ruta_png}")


def graficar_distribucion_apilada(df, variable_A, variable_B, variable_C, funcion_agregada, carpeta_salida):
    seccion("Distribucion apilada")

    columnas = [variable_A, variable_B, variable_C]
    faltantes = [columna for columna in columnas if columna not in df.columns]
    if faltantes:
        print(f"No se genera distribucion apilada. Columnas faltantes: {faltantes}")
        return

    tabla_pivote = df[columnas].pivot_table(
        index=variable_A,
        columns=variable_B,
        values=variable_C,
        aggfunc=funcion_agregada,
        fill_value=0
    )

    tabla(f"Tabla base de {variable_A} vs {variable_B}", tabla_pivote.reset_index(), max_filas=30)

    ax = tabla_pivote.plot(kind="bar", stacked=True, figsize=(10, 6))
    ax.set_title(f"Distribucion apilada: {variable_A} vs {variable_B}")
    ax.set_xlabel(variable_A)
    ax.set_ylabel("Conteo" if funcion_agregada == "count" else funcion_agregada)
    ax.grid(axis="y", alpha=0.25)
    plt.xticks(rotation=45, ha="right")
    plt.legend(title=variable_B, bbox_to_anchor=(1.02, 1), loc="upper left")
    plt.tight_layout()

    ruta_png = carpeta_salida / f"{_prefijo_archivo(df)}_distribucion_{_nombre_archivo(variable_A)}_{_nombre_archivo(variable_B)}.png"
    plt.savefig(ruta_png, dpi=180)
    plt.close()
    print(f"Imagen guardada: {ruta_png}")


def ejecutar_perfilado(
    archivo,
    encoding_archivo,
    separador_archivo,
    histogramas_a_generar,
    columnas_numericas_boxplot,
    columnas_categoricas,
    variable_A,
    variable_B,
    variable_C,
    funcion_agregada
):
    df = cargar_datos(archivo, encoding=encoding_archivo, sep=separador_archivo)
    df.attrs["archivo_origen"] = str(archivo)
    carpeta_salida = _carpeta_salida()

    titulo("Perfilado de datos")
    metrica("Archivo analizado", archivo)
    metrica("Encoding", encoding_archivo)
    metrica("Separador", separador_archivo)
    metrica("Carpeta de salidas", carpeta_salida)

    mostrar_estructura(df)
    generar_perfil_columnas(df)
    graficar_histogramas(df, columnas=histogramas_a_generar, carpeta_salida=carpeta_salida)
    generar_boxplot_y_resumen(df, columnas=columnas_numericas_boxplot, carpeta_salida=carpeta_salida)
    graficar_frecuencias_categoricas(df, columnas=columnas_categoricas, carpeta_salida=carpeta_salida)
    graficar_distribucion_apilada(
        df,
        variable_A=variable_A,
        variable_B=variable_B,
        variable_C=variable_C,
        funcion_agregada=funcion_agregada,
        carpeta_salida=carpeta_salida
    )
