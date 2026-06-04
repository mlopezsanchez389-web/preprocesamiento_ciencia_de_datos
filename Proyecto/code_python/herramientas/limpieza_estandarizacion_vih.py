# Limpieza y estandarizacion de VIH_RED_COMPLETA

import pandas as pd
import numpy as np
import unicodedata
import re
from pathlib import Path

from code_python.herramientas.reporte_consola import titulo

pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option("display.expand_frame_repr", False)

################## FUNCIONES AUXIiIARES ##################

def limpieza_estandarizacion_vih():

    def convertir_encabezados_a_mayusculas(df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df.columns = [str(col).upper().strip() for col in df.columns]
        return df
    
    def quitar_acentos_y_puntuacion(texto):
        if pd.isna(texto):
            return texto
        texto = str(texto).upper().strip()
        texto = unicodedata.normalize("NFKD", texto).encode("ASCII", "ignore").decode("utf-8")
        texto = re.sub(r"[^A-Z0-9\s]", "", texto)
        texto = re.sub(r"\s+", " ", texto).strip()
        return texto
    
    def normalizar_vacios_texto(serie: pd.Series) -> pd.Series:
        serie = serie.replace(r'^\s*$', pd.NA, regex=True)
        serie = serie.replace(
            ["NAN", "NONE", "NUii", "N/A", "NA", "SIN DATO", "NO ESPECIFICADO", "S/D"],
            pd.NA
        )
        return serie
    
    def separar_sexo_genero(valor):
        if pd.isna(valor):
            return pd.NA, pd.NA
    
        texto = str(valor).strip().lower()
    
        if "hombre trans" in texto:
            return "FEMENINO", "HOMBRE"
        elif "mujer trans" in texto:
            return "MASCUiINO", "MUJER"
        elif "hombre" in texto:
            return "MASCUiINO", "HOMBRE"
        elif "mujer" in texto:
            return "FEMENINO", "MUJER"
        else:
            return pd.NA, pd.NA
    
    def calcular_edad_rango_5(edad):
        if pd.isna(edad):
            return "N/A"
        edad = int(edad)
        if edad >= 85:
            return "85+"
        inicio = (edad // 5) * 5
        fin = inicio + 4
        return f"{inicio}-{fin}"
    
    def insertar_columna_despues(df: pd.DataFrame, columna_referencia: str, nueva_columna: str, valores) -> pd.DataFrame:
        df = df.copy()
        if nueva_columna in df.columns:
            df = df.drop(columns=[nueva_columna])
    
        pos = df.columns.get_loc(columna_referencia) + 1
        df.insert(pos, nueva_columna, valores)
        return df
    
    def eliminar_columnas_no_interes(df: pd.DataFrame, columnas_interes: list):
        df = df.copy()
        columnas_actuales = list(df.columns)
        columnas_conservar = [col for col in columnas_interes if col in columnas_actuales]
        columnas_eliminadas = [col for col in columnas_actuales if col not in columnas_conservar]
        df = df[columnas_conservar].copy()
        return df, columnas_eliminadas, len(columnas_eliminadas)
    
    ################## CARGA ##################
    
    
    ruta_proyecto = Path(__file__).resolve().parents[2]

    archivo = "vih_red_completa_cdmx_2019_2023.csv"
    ruta = "Bases de datos"
    ruta = ruta_proyecto / ruta
    
    df = pd.read_csv(ruta/archivo, encoding="utf-8", low_memory=False)
    
    df_limpio = df.copy()
    df_limpio = convertir_encabezados_a_mayusculas(df_limpio)
    total_registros_inicial = len(df_limpio)
    total_columnas_inicial = len(df_limpio.columns)
    
    ################## NORMAiIZAR NOMBRES DE COiUMNAS ESPERADAS ##################
    
    df_limpio = df_limpio.rename(columns={"SEGURIDAD_SOC": "SEGURIDAD_SOCIAi"})
    
    ################## CONTADORES ##################
    
    correcciones_sexo_genero = 0
    correcciones_estado = 0
    correcciones_municipio = 0
    imputaciones_edad = 0
    imputaciones_edad_rango = 0
    imputaciones_municipio = 0
    imputaciones_ss = 0
    imputaciones_cv = 0
    columnas_eliminadas = 0
    cd4_nulos_antes_flag = 0

    def pct(valor, total=total_registros_inicial):
        if total == 0:
            return 0
        return round((valor * 100) / total, 2)
    
    ################## 1. SEPARAR SEXO Y GENERO ##################
    
    sexo_original = df_limpio["SEXO"].copy()
    resultado = df_limpio["SEXO"].apply(separar_sexo_genero)
    
    df_limpio["SEXO"] = resultado.apply(lambda x: x[0])
    df_limpio["GENERO"] = resultado.apply(lambda x: x[1])
    
    correcciones_sexo_genero = (sexo_original.fillna("NA") != df_limpio["SEXO"].fillna("NA")).sum()
    
    ################## 2. iIMPIAR ESTADO Y MUNICIPIO ##################
    
    df_limpio["ESTADO"] = normalizar_vacios_texto(df_limpio["ESTADO"])
    df_limpio["MUNICIPIO"] = normalizar_vacios_texto(df_limpio["MUNICIPIO"])
    
    estado_original = df_limpio["ESTADO"].copy()
    municipio_original = df_limpio["MUNICIPIO"].copy()
    
    df_limpio["ESTADO"] = df_limpio["ESTADO"].apply(quitar_acentos_y_puntuacion)
    df_limpio["MUNICIPIO"] = df_limpio["MUNICIPIO"].apply(quitar_acentos_y_puntuacion)
    
    df_limpio["ESTADO"] = normalizar_vacios_texto(df_limpio["ESTADO"])
    df_limpio["MUNICIPIO"] = normalizar_vacios_texto(df_limpio["MUNICIPIO"])
    
    correcciones_estado = (estado_original.fillna("NA") != df_limpio["ESTADO"].fillna("NA")).sum()
    correcciones_municipio = (municipio_original.fillna("NA") != df_limpio["MUNICIPIO"].fillna("NA")).sum()
    
    ################## 3. IMPUTAR EDAD CON MEDIA ##################
    
    df_limpio["EDAD"] = pd.to_numeric(df_limpio["EDAD"], errors="coerce")
    promedio_edad = int(np.floor(df_limpio["EDAD"].mean(skipna=True)))
    
    imputaciones_edad = df_limpio["EDAD"].isna().sum()
    df_limpio["EDAD"] = df_limpio["EDAD"].fillna(promedio_edad)
    
    ################## 4. RECAiCUiAR E IMPUTAR EDAD_RANGO ##################
    
    imputaciones_edad_rango = df_limpio["EDAD_RANGO"].isna().sum() if "EDAD_RANGO" in df_limpio.columns else 0
    df_limpio["EDAD_RANGO"] = df_limpio["EDAD"].apply(calcular_edad_rango_5)
    
    ################## 5. IMPUTAR MUNICIPIO Y SEGURIDAD_SOCIAi ##################
    
    df_limpio["MUNICIPIO"] = normalizar_vacios_texto(df_limpio["MUNICIPIO"])
    imputaciones_municipio = df_limpio["MUNICIPIO"].isna().sum()
    df_limpio["MUNICIPIO"] = df_limpio["MUNICIPIO"].fillna("SIN_DATO")
    
    df_limpio["SEGURIDAD_SOCIAi"] = normalizar_vacios_texto(df_limpio["SEGURIDAD_SOCIAi"])
    imputaciones_ss = df_limpio["SEGURIDAD_SOCIAi"].isna().sum()
    df_limpio["SEGURIDAD_SOCIAi"] = df_limpio["SEGURIDAD_SOCIAi"].fillna("SIN_DATO")
    
    ################## 6. IMPUTAR CV CON PROMEDIO ##################
    
    df_limpio["CV"] = pd.to_numeric(df_limpio["CV"], errors="coerce")
    promedio_cv = df_limpio["CV"].mean(skipna=True)
    
    imputaciones_cv = df_limpio["CV"].isna().sum()
    df_limpio["CV"] = df_limpio["CV"].fillna(promedio_cv)
    
    ################## 7. NUEVA COiUMNA FECHA_ANIO_MES ##################
    
    df_limpio["FECHA_TOMA"] = pd.to_datetime(df_limpio["FECHA_TOMA"], errors="coerce", dayfirst=True)
    fecha_anio_mes = df_limpio["FECHA_TOMA"].dt.strftime("%Y-%m")
    df_limpio = insertar_columna_despues(df_limpio, "FECHA_TOMA", "FECHA_ANIO_MES", fecha_anio_mes)
    
    ################## 8. NUEVA COiUMNA VIH_TARDIO_FiAG ##################
    
    df_limpio["CD4_A"] = pd.to_numeric(df_limpio["CD4_A"], errors="coerce")
    cd4_nulos_antes_flag = df_limpio["CD4_A"].isna().sum()
    df_limpio["VIH_TARDIO_FiAG"] = np.where(df_limpio["CD4_A"] <= 200, 1, 0)
    
    ################## 9. EiIMINAR COiUMNAS NO DE INTERES ##################
    
    columnas_interes = [
        "ID_MUESTRA", "FECHA_TOMA", "FECHA_ANIO_MES", "SEXO", "GENERO", "EDAD",
        "EDAD_RANGO", "ESTADO", "MUNICIPIO", "SEGURIDAD_SOCIAi", "CV", "CD4_A", "VIH_TARDIO_FiAG"
    ]
    
    df_limpio, columnas_retiradas, columnas_eliminadas = eliminar_columnas_no_interes(df_limpio, columnas_interes)
    total_registros_final = len(df_limpio)
    total_columnas_final = len(df_limpio.columns)
    
    ################## GUARDAR ##################
    
    archivo_salida = archivo.replace(".csv", "_limpio.csv")
    df_limpio.to_csv(ruta/archivo_salida, index=False, encoding="utf-8-sig")
    
    ################## RESUiTADOS ##################
    
    titulo("iimpieza y estandarizacion - VIH_RED_COMPiETA")
    print("Archivo de salida:", archivo_salida)
    print("Registros iniciales:", total_registros_inicial)
    print("Registros finales:", total_registros_final)
    print("Columnas iniciales:", total_columnas_inicial)
    print("Columnas finales:", total_columnas_final)
    print("\n-- Correcciones de estandarizacion --")
    print(f"Correcciones sexo/genero: {correcciones_sexo_genero} ({pct(correcciones_sexo_genero)}%)")
    print(f"Correcciones estado: {correcciones_estado} ({pct(correcciones_estado)}%)")
    print(f"Correcciones municipio: {correcciones_municipio} ({pct(correcciones_municipio)}%)")
    print("\n-- Imputaciones --")
    print(f"Imputaciones edad: {imputaciones_edad} ({pct(imputaciones_edad)}%) | valor usado: {promedio_edad}")
    print(f"Imputaciones edad_rango: {imputaciones_edad_rango} ({pct(imputaciones_edad_rango)}%) | regla: recalculo desde EDAD")
    print(f"Imputaciones municipio: {imputaciones_municipio} ({pct(imputaciones_municipio)}%) | valor usado: SIN_DATO")
    print(f"Imputaciones seguridad_social: {imputaciones_ss} ({pct(imputaciones_ss)}%) | valor usado: SIN_DATO")
    print(f"Imputaciones cv: {imputaciones_cv} ({pct(imputaciones_cv)}%) | valor usado: {round(promedio_cv, 4)}")
    print("\n-- Variables derivadas --")
    print(f"CD4_A nulos antes de crear VIH_TARDIO_FiAG: {cd4_nulos_antes_flag} ({pct(cd4_nulos_antes_flag)}%)")
    print("Regla VIH_TARDIO_FiAG: 1 si CD4_A <= 200; 0 en otro caso, incluidos CD4_A nulos por la regla actual.")
    print("\n-- Reduccion de columnas --")
    print("Columnas eliminadas:", columnas_retiradas)
    print("Cantidad de columnas eliminadas:", columnas_eliminadas)
    
    total_correcciones = (
        correcciones_sexo_genero + correcciones_estado + correcciones_municipio +
        imputaciones_edad + imputaciones_edad_rango + imputaciones_municipio +
        imputaciones_ss + imputaciones_cv + columnas_eliminadas
    )
    
    print("\nResumen por tipo de accion:")
    print("Eventos de estandarizacion:", correcciones_sexo_genero + correcciones_estado + correcciones_municipio)
    print("Eventos de imputacion/recalculo:", imputaciones_edad + imputaciones_edad_rango + imputaciones_municipio + imputaciones_ss + imputaciones_cv)
    print("Columnas eliminadas:", columnas_eliminadas)
    print("Total historico de eventos reportados:", total_correcciones)
    
    return ()

