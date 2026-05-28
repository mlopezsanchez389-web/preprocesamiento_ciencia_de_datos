# Limpieza y estandarización de REGISTRO_DEFUNCIONES
# Archivo de entrada: defunciones_registradas_2019_2023_cdmx_columnas_comunes.csv
# Archivo de salida: defunciones_registradas_2019_2023_cdmx_columnas_comunes_limpio.csv

import pandas as pd
import numpy as np
import re
from pathlib import Path

pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option("display.expand_frame_repr", False)

################## FUNCIONES AUXILIARES ##################

def limpieza_estandarizacion_defunciones():

    def convertir_encabezados_a_mayusculas(df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df.columns = [str(col).upper().strip() for col in df.columns]
        return df
    
    def agregar_id_consecutivo(df: pd.DataFrame, nombre_columna: str = "ID_REGISTRO_DEF") -> pd.DataFrame:
        df = df.copy()
        df[nombre_columna] = range(1, len(df) + 1)
        return df
    
    def convertir_vacios_a_na(df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        return df.replace(r'^\s*$', pd.NA, regex=True)
    
    def calcular_edad_anios(fecha_nac, fecha_ocurr):
        if pd.isna(fecha_nac) or pd.isna(fecha_ocurr):
            return np.nan
    
        edad = fecha_ocurr.year - fecha_nac.year
        if (fecha_ocurr.month, fecha_ocurr.day) < (fecha_nac.month, fecha_nac.day):
            edad -= 1
    
        return int(edad)
    
    def calcular_edad_rango_5(edad):
        if pd.isna(edad):
            return "N/A"
        edad = int(edad)
        if edad >= 85:
            return "85+"
        inicio = (edad // 5) * 5
        fin = inicio + 4
        return f"{inicio}-{fin}"
    
    def detectar_vih(codigo):
        if pd.isna(codigo):
            return 0
        texto = str(codigo).upper().strip()
        if re.match(r"^B2[0-4]", texto):
            return 1
        return 0
    
    def insertar_columna_despues(df: pd.DataFrame, columna_referencia: str, nueva_columna: str, valores) -> pd.DataFrame:
        df = df.copy()
        if nueva_columna in df.columns:
            df = df.drop(columns=[nueva_columna])
    
        pos = df.columns.get_loc(columna_referencia) + 1
        df.insert(pos, nueva_columna, valores)
        return df
    
    def eliminar_columnas_no_interes(df: pd.DataFrame, columnas_interes: list) -> tuple[pd.DataFrame, int]:
        df = df.copy()
        columnas_actuales = list(df.columns)
        columnas_conservar = [col for col in columnas_interes if col in columnas_actuales]
        columnas_eliminadas = [col for col in columnas_actuales if col not in columnas_conservar]
        df = df[columnas_conservar].copy()
        return df, columnas_eliminadas, len(columnas_eliminadas)
    
    ################## CARGA ##################

    ruta_proyecto = Path(__file__).resolve().parents[2]

    archivo = "defunciones_registradas_cdmx_2019_2023.csv"
    ruta = "Bases de datos"
    ruta = ruta_proyecto / ruta
    
    df = pd.read_csv(ruta/archivo, encoding="utf-8", low_memory=False)
    
    df_limpio = df.copy()
    df_limpio = convertir_encabezados_a_mayusculas(df_limpio)
    df_limpio = convertir_vacios_a_na(df_limpio)
    
    ################## CONTADORES ##################
    
    vacios_generales = 0
    filas_eliminadas_por_fecha = 0
    columnas_eliminadas = 0
    edad_recalculada = 0
    filas_eliminadas_por_edad_vacia = 0
    
    ################## 1. CONTAR VACIOS ##################
    
    vacios_generales = df_limpio.isna().sum().sum()
    
    ################## 2. CONVERTIR FECHAS ##################
    
    columnas_fecha = ["FECHA_OCURR", "FECHA_NACIM", "FECHA_REGIS", "FECHA_CERT"]
    
    for col in columnas_fecha:
        if col in df_limpio.columns:
            df_limpio[col] = pd.to_datetime(df_limpio[col], errors="coerce", dayfirst=True)
    
    ################## 3. ELIMINAR FECHA_OCURR ANTERIORES A 2019 ##################
    
    filas_antes = len(df_limpio)
    df_limpio = df_limpio[df_limpio["FECHA_OCURR"].dt.year >= 2019].copy()
    filas_eliminadas_por_fecha = filas_antes - len(df_limpio)
    
    ################## 4. RECALCULAR EDAD A PARTIR DE FECHA_OCURR - FECHA_NACIM ##################
    
    edad_original_nulos = df_limpio["EDAD"].isna().sum() if "EDAD" in df_limpio.columns else 0
    
    df_limpio["EDAD"] = df_limpio.apply(
        lambda fila: calcular_edad_anios(fila["FECHA_NACIM"], fila["FECHA_OCURR"]),
        axis=1
    )
    
    edad_recalculada = df_limpio["EDAD"].notna().sum()
    
    ################## 4.1 ELIMINAR FILAS DONDE EDAD SIGA VACIA ##################
    
    filas_antes_edad_vacia = len(df_limpio)
    df_limpio = df_limpio[df_limpio["EDAD"].notna()].copy()
    filas_eliminadas_por_edad_vacia = filas_antes_edad_vacia - len(df_limpio)
    
    ################## 5. CREAR EDAD_RANGO ##################
    
    df_limpio["EDAD_RANGO"] = df_limpio["EDAD"].apply(calcular_edad_rango_5)
    
    ################## 6. CREAR FECHA_ANIO_MES ##################
    
    fecha_anio_mes = df_limpio["FECHA_OCURR"].dt.strftime("%Y-%m")
    df_limpio = insertar_columna_despues(df_limpio, "FECHA_OCURR", "FECHA_ANIO_MES", fecha_anio_mes)
    
    ################## 7. CREAR VIH_FLAG ##################
    
    df_limpio["VIH_FLAG"] = df_limpio["CAUSA_DEF"].apply(detectar_vih)
    
    ################## 7. NUEVA COLUMNA ID ##################
    
    df_limpio = agregar_id_consecutivo(df_limpio, "ID_REGISTRO_DEF")
    cols = ["ID_REGISTRO_DEF"] + [col for col in df_limpio.columns if col != "ID_REGISTRO_DEF"]
    df_limpio = df_limpio[cols]
    
    ################## 8. DEVOLVER FECHAS A TEXTO ##################
    
    for col in columnas_fecha:
        if col in df_limpio.columns:
            df_limpio[col] = df_limpio[col].dt.strftime("%Y-%m-%d")
    
    ################## 9. ELIMINAR COLUMNAS NO DE INTERES ##################
    
    # Variables base pedidas + variables extra relevantes
    columnas_interes = [
        "ID_REGISTRO_DEF","FECHA_OCURR", "FECHA_ANIO_MES", "ANIO_OCUR", "MES_OCURR",
        "CAUSA_DEF", "LISTA_MEX", "SEXO", "EDAD", "EDAD_RANGO", "ENT_RESID",
        "FECHA_NACIM", "ENT_OCURR", "ENT_REGIS",
        "MUN_RESID", "MUN_OCURR", "LUGAR_OCUR", "ASIST_MEDI", "DERECHOHAB",
        "VIH_FLAG"
    ]
    
    df_limpio, columnas_retiradas, columnas_eliminadas = eliminar_columnas_no_interes(df_limpio, columnas_interes)
    
    ################## GUARDAR ##################
    
    archivo_salida = archivo.replace(".csv", "_limpio.csv")
    df_limpio.to_csv(ruta/archivo_salida, index=False, encoding="utf-8-sig")
    
    ################## RESULTADOS ##################
    
    print("##################################################")
    print("LIMPIEZA REGISTRO_DEFUNCIONES")
    print("##################################################\n")
    
    print("Archivo de salida:", archivo_salida)
    print("Vacíos detectados como NA:", vacios_generales)
    print("Filas eliminadas por FECHA_OCURR anterior a 2019:", filas_eliminadas_por_fecha)
    print("Registros con edad recalculada:", edad_recalculada)
    print("Columnas eliminadas:", columnas_retiradas)
    print("Cantidad de columnas eliminadas:", columnas_eliminadas)
    
    total_correcciones = vacios_generales + filas_eliminadas_por_fecha + columnas_eliminadas+filas_eliminadas_por_edad_vacia 
    print("Total de correcciones realizadas:", total_correcciones)
    
    return ()