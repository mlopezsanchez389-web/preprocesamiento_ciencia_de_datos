# Limpieza y estandarizacion de CONSULTAS_OTORGADAS_HGM
# Archivo de entrada: CONSULTAS_OTORGADAS_2019_2023_cdmx_unificado VFF.csv

import pandas as pd
import numpy as np
import unicodedata
import re

from pathlib import Path

from code_python.herramientas.reporte_consola import titulo

pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option("display.expand_frame_repr", False)

################## FUNCIONES AUXILIARES ##################

def limpieza_estandarizacion_consultas_hospital():
        
    def convertir_encabezados_a_mayusculas(df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df.columns = [str(col).upper().strip() for col in df.columns]
        return df
    
    def agregar_id_consecutivo(df: pd.DataFrame, nombre_columna: str = "ID_REGISTRO") -> pd.DataFrame:
        df = df.copy()
        df[nombre_columna] = range(1, len(df) + 1)
        return df
    
    def normalizar_sexo_hgm(valor):
        if pd.isna(valor):
            return valor
    
        texto = str(valor).strip().upper()
    
        if "MASCULINO" in texto:
            return "MASCULINO"
        elif "FEMENINO" in texto:
            return "FEMENINO"
        else:
            return valor
    
    def limpiar_texto_mayus(texto):
        if pd.isna(texto):
            return texto
        texto = str(texto).upper().strip()
        texto = unicodedata.normalize("NFKD", texto).encode("ASCII", "ignore").decode("utf-8")
        texto = re.sub(r"[^A-Z0-9\s]", "", texto)
        texto = re.sub(r"\s+", " ", texto).strip()
        return texto
    
    def detectar_vih(codigo):
        if pd.isna(codigo):
            return 0
        texto = str(codigo).upper().strip()
        if re.match(r"^B2[0-4]", texto):
            return 1
        return 0
    
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
    
    def eliminar_columnas_no_interes(df: pd.DataFrame, columnas_interes: list) -> tuple[pd.DataFrame, int]:
        df = df.copy()
        columnas_actuales = list(df.columns)
        columnas_conservar = [col for col in columnas_interes if col in columnas_actuales]
        columnas_eliminadas = [col for col in columnas_actuales if col not in columnas_conservar]
        df = df[columnas_conservar].copy()
        return df, columnas_eliminadas, len(columnas_eliminadas)
    
    ################## CARGA ##################
    
    ruta_proyecto = Path(__file__).resolve().parents[2]

    archivo = "consultas_HGM_cdmx_2019_2023.csv"
    ruta = "Bases de datos"
    ruta = ruta_proyecto / ruta
    
    df = pd.read_csv(ruta/archivo, encoding="utf-8", low_memory=False)
    
    df_limpio = df.copy()
    df_limpio["SEXO"] = df_limpio["SEXO"].apply(normalizar_sexo_hgm)
    df_limpio = convertir_encabezados_a_mayusculas(df_limpio)
    total_registros_inicial = len(df_limpio)
    total_columnas_inicial = len(df_limpio.columns)
    
    ################## CONTADORES ##################
    
    imputaciones_categoricas = 0
    imputaciones_edad = 0
    correcciones_descripcion = 0
    columnas_eliminadas = 0
    filas_eliminadas_edad_negativa = 0
    imputaciones_categoricas_por_columna = {}

    def pct(valor, total=total_registros_inicial):
        if total == 0:
            return 0
        return round((valor * 100) / total, 2)
    
    ################## 1. IMPUTAR CATEGORICOS COMO N/A ##################
    
    columnas_categoricas = [
        "TIPO_CONSULTA", "PROCEDENCIA", "SEXO", "ESPECIALIDAD",
        "CODIGO", "DESCRIPCION_DIAGNOSTICO"
    ]
    
    for columna in columnas_categoricas:
        df_limpio[columna] = df_limpio[columna].replace(r'^\s*$', pd.NA, regex=True)
        nulos_columna = df_limpio[columna].isna().sum()
        imputaciones_categoricas_por_columna[columna] = int(nulos_columna)
        imputaciones_categoricas += nulos_columna
        df_limpio[columna] = df_limpio[columna].fillna("N/A")
    
    ################## 2. IMPUTAR EDAD CON PROMEDIO REDONDEADO ##################
    
    df_limpio["EDAD"] = pd.to_numeric(df_limpio["EDAD"], errors="coerce")
    filas_eliminadas_edad_negativa = (df_limpio["EDAD"].notna() & (df_limpio["EDAD"] < 0)).sum()
    df_limpio = df_limpio[df_limpio["EDAD"].isna() | (df_limpio["EDAD"] >= 0)].copy()
    
    promedio_edad = int(np.floor(df_limpio["EDAD"].mean(skipna=True)))
    
    imputaciones_edad = df_limpio["EDAD"].isna().sum()
    df_limpio["EDAD"] = df_limpio["EDAD"].fillna(promedio_edad)
    
    ################## 3. LIMPIAR DESCRIPCION_DIAGNOSTICO ##################
    
    descripcion_original = df_limpio["DESCRIPCION_DIAGNOSTICO"].copy()
    df_limpio["DESCRIPCION_DIAGNOSTICO"] = df_limpio["DESCRIPCION_DIAGNOSTICO"].apply(limpiar_texto_mayus)
    
    correcciones_descripcion = (
        descripcion_original.fillna("NA") != df_limpio["DESCRIPCION_DIAGNOSTICO"].fillna("NA")
    ).sum()
    
    ################## 4. NUEVA COLUMNA VIH_FLAG ##################
    
    df_limpio["VIH_FLAG"] = df_limpio["CODIGO"].apply(detectar_vih)
    
    ################## 5. NUEVA COLUMNA EDAD_RANGO ##################
    
    df_limpio["EDAD_RANGO"] = df_limpio["EDAD"].apply(calcular_edad_rango_5)
    
    ################## 6. NUEVA COLUMNA FECHA_ANIO_MES ##################
    
    df_limpio["FECHA"] = pd.to_datetime(df_limpio["FECHA"], errors="coerce", dayfirst=True)
    fecha_anio_mes = df_limpio["FECHA"].dt.strftime("%Y-%m")
    df_limpio = insertar_columna_despues(df_limpio, "FECHA", "FECHA_ANIO_MES", fecha_anio_mes)
    
    ################## 7. NUEVA COLUMNA ID ##################
    
    df_limpio = agregar_id_consecutivo(df_limpio, "ID_REGISTRO")
    cols = ["ID_REGISTRO"] + [col for col in df_limpio.columns if col != "ID_REGISTRO"]
    df_limpio = df_limpio[cols]
    
    ################## 7. ELIMINAR COLUMNAS NO DE INTERES ##################
    
    columnas_interes = [
        "ID_REGISTRO","FECHA", "FECHA_ANIO_MES", "TIPO_CONSULTA", "PROCEDENCIA", "SEXO",
        "EDAD", "EDAD_RANGO", "ESPECIALIDAD", "CODIGO", "DESCRIPCION_DIAGNOSTICO", "VIH_FLAG"
    ]
    
    df_limpio, columnas_retiradas, columnas_eliminadas = eliminar_columnas_no_interes(df_limpio, columnas_interes)
    total_registros_final = len(df_limpio)
    total_columnas_final = len(df_limpio.columns)
    
    ################## GUARDAR ##################
    
    archivo_salida = archivo.replace(".csv", "_limpio.csv")
    df_limpio.to_csv(ruta/archivo_salida, index=False, encoding="utf-8-sig")
    
    ################## RESULTADOS ##################
    
    titulo("Limpieza y estandarizacion - CONSULTAS HGM")
    print("Archivo de salida:", archivo_salida)
    print("Registros iniciales:", total_registros_inicial)
    print("Registros finales:", total_registros_final)
    print("Columnas iniciales:", total_columnas_inicial)
    print("Columnas finales:", total_columnas_final)
    print("\n-- Detalle de imputaciones categoricas --")
    print(f"Valor usado para categoricas faltantes: N/A")
    for columna, total in imputaciones_categoricas_por_columna.items():
        print(f"- {columna}: {total} ({pct(total)}%)")
    print("\n-- Detalle de edad --")
    print(f"Filas eliminadas por EDAD negativa: {filas_eliminadas_edad_negativa} ({pct(filas_eliminadas_edad_negativa)}%)")
    print(f"Valor usado para imputar EDAD: {promedio_edad}")
    print(f"Porcentaje imputado en EDAD: {pct(imputaciones_edad, total_registros_final)}%")
    print("\n-- Detalle de correcciones --")
    print(f"Porcentaje descripcion_diagnostico corregido: {pct(correcciones_descripcion, total_registros_final)}%")
    print("Imputaciones categoricas:", imputaciones_categoricas)
    print("Imputaciones edad:", imputaciones_edad)
    print("Correcciones descripcion_diagnostico:", correcciones_descripcion)
    print("Cantidad de columnas eliminadas:", columnas_eliminadas)
    print("Columnas eliminadas:", columnas_retiradas)
    
    
    total_correcciones = imputaciones_categoricas + imputaciones_edad + correcciones_descripcion + columnas_eliminadas + filas_eliminadas_edad_negativa
    print("\nResumen por tipo de accion:")
    print("Eventos de imputacion:", imputaciones_categoricas + imputaciones_edad)
    print("Eventos de correccion de texto:", correcciones_descripcion)
    print("Filas eliminadas:", filas_eliminadas_edad_negativa)
    print("Columnas eliminadas:", columnas_eliminadas)
    print("Total historico de eventos reportados:", total_correcciones)
    
    return ()

