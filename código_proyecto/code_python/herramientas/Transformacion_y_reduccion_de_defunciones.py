
import pandas as pd
import numpy as np
import re
from scipy.stats import chi2_contingency
from pathlib import Path

pd.set_option("display.max_rows", None)
pd.set_option("display.max_columns", None)
pd.set_option("display.expand_frame_repr", False)


def transformar_reducir_defunciones():

    def convertir_encabezados_a_mayusculas(df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df.columns = [str(col).upper().strip() for col in df.columns]
        return df
    
    def insertar_columna_despues(df: pd.DataFrame, columna_referencia: str, nueva_columna: str, valores) -> pd.DataFrame:
        df = df.copy()
        if nueva_columna in df.columns:
            df = df.drop(columns=[nueva_columna])
        pos = df.columns.get_loc(columna_referencia) + 1
        df.insert(pos, nueva_columna, valores)
        return df
    
    def mapear_sexo_genero_binario(serie: pd.Series) -> pd.Series:
        s = serie.astype("string").str.strip().str.upper()
        mapa = {
            "MASCULINO": 1, "HOMBRE": 1, "1": 1,
            "FEMENINO": 0, "MUJER": 0, "2": 0
        }
        return s.map(mapa)
    
    def mapear_seguridad_social_binario(serie: pd.Series) -> pd.Series:
        s = serie.astype("string").str.strip().str.upper()
        faltantes = {"", "NAN", "NONE", "<NA>", "NA", "N/A", "SIN_DATO", "DESCONOCE", "DESCONOCIDO"}
        return s.apply(lambda x: 0 if x in faltantes else 1).astype("Int64")
    
    def mapear_edad_rango_ordinal(serie: pd.Series) -> pd.Series:
        s = serie.astype("string").str.strip().str.upper()
    
        def convertir(valor):
            if valor in {"NAN", "NONE", "<NA>", "SIN_DATO", "N/A", "NA", ""}:
                return np.nan
            valor = valor.replace(" A ", "-").replace("–", "-").replace("—", "-").strip()
            numeros = re.findall(r"\d+", valor)
            if len(numeros) == 0:
                return np.nan
            inicio = int(numeros[0])
            return int(inicio / 5) + 1
    
        return s.apply(convertir)
    
    def escalar_0_1(serie: pd.Series) -> pd.Series:
        s = pd.to_numeric(serie, errors="coerce")
        minimo = s.min()
        maximo = s.max()
        if pd.isna(minimo) or pd.isna(maximo) or minimo == maximo:
            return pd.Series(np.zeros(len(s)), index=s.index, dtype="float64")
        return (s - minimo) / (maximo - minimo)
    
    def escalar_edad_0_130(serie: pd.Series) -> pd.Series:
        s = pd.to_numeric(serie, errors="coerce")
        return (s / 130).clip(lower=0, upper=1)
    
    def transformar_cv_exp10_y_escalar(serie: pd.Series) -> pd.Series:
        s = pd.to_numeric(serie, errors="coerce")
        s = np.power(10.0, s)
        minimo = np.nanmin(s)
        maximo = np.nanmax(s)
        if np.isnan(minimo) or np.isnan(maximo) or minimo == maximo:
            return pd.Series(np.zeros(len(s)), index=serie.index, dtype="float64")
        return pd.Series((s - minimo) / (maximo - minimo), index=serie.index)
    
    def frecuencia_absoluta_entera(serie: pd.Series) -> pd.Series:
        s = serie.astype("string").fillna("SIN_DATO")
        frec = s.value_counts(dropna=False)
        return s.map(frec).astype("Int64")
    
    def convertir_fecha_anio_mes_a_orden(serie: pd.Series) -> pd.Series:
        fecha = pd.to_datetime(serie.astype("string") + "-01", errors="coerce")
        return (fecha.dt.year * 12 + fecha.dt.month).astype("Int64")
    
    def eliminar_columnas(df: pd.DataFrame, columnas_eliminar: list):
        df = df.copy()
        presentes = [c for c in columnas_eliminar if c in df.columns]
        df = df.drop(columns=presentes, errors="ignore")
        return df, presentes
    
    def detectar_redundancia_pearson(df: pd.DataFrame, columna_objetivo: str, columnas_excluir: list, umbral: float = 0.95):
        columnas_numericas = [
            c for c in df.select_dtypes(include=[np.number]).columns
            if c != columna_objetivo and c not in columnas_excluir
        ]
    
        pares = []
        columnas_sugeridas = set()
    
        if len(columnas_numericas) < 2:
            return pares, columnas_sugeridas
    
        corr = df[columnas_numericas].corr(method="pearson").abs()
    
        for i in range(len(columnas_numericas)):
            for j in range(i + 1, len(columnas_numericas)):
                c1 = columnas_numericas[i]
                c2 = columnas_numericas[j]
                valor = corr.loc[c1, c2]
    
                if pd.notna(valor) and valor >= umbral:
                    pares.append((c1, c2, float(valor)))
                    columnas_sugeridas.add(c2)
    
        return pares, columnas_sugeridas
    
    def cramers_v(tabla: pd.DataFrame):
        chi2, _, _, _ = chi2_contingency(tabla)
        n = tabla.to_numpy().sum()
        r, k = tabla.shape
        if n == 0 or min(r, k) <= 1:
            return np.nan
        return np.sqrt((chi2 / n) / (min(r - 1, k - 1)))
    
    def detectar_redundancia_chi2(df: pd.DataFrame, columna_objetivo: str, columnas_excluir: list, umbral_v: float = 0.95, max_unicos: int = 20):
        columnas_discretas = []
    
        for c in df.select_dtypes(include=[np.number]).columns:
            if c == columna_objetivo or c in columnas_excluir:
                continue
            nun = df[c].nunique(dropna=True)
            if nun <= max_unicos:
                columnas_discretas.append(c)
    
        pares = []
        columnas_sugeridas = set()
    
        for i in range(len(columnas_discretas)):
            for j in range(i + 1, len(columnas_discretas)):
                c1 = columnas_discretas[i]
                c2 = columnas_discretas[j]
    
                tabla = pd.crosstab(df[c1], df[c2])
                if tabla.shape[0] < 2 or tabla.shape[1] < 2:
                    continue
    
                chi2, p, _, _ = chi2_contingency(tabla)
                v = cramers_v(tabla)
    
                if pd.notna(v) and v >= umbral_v:
                    pares.append((c1, c2, float(chi2), float(p), float(v)))
                    columnas_sugeridas.add(c2)
    
        return pares, columnas_sugeridas


    ruta_proyecto = Path(__file__).resolve().parents[2]

    archivo = "defunciones_registradas_cdmx_2019_2023_limpio_sin_duplicados.csv"
    ruta = "Bases de datos"
    ruta = ruta_proyecto / ruta
    
    archivo = ruta/archivo
    archivo_salida = archivo.with_stem(archivo.stem + "_transformado")  
    

    columna_objetivo = "VIH_FLAG"
    eliminar_redundantes = True
    umbral_redundancia = 0.95
    
    df = pd.read_csv(archivo, encoding="utf-8", low_memory=False)
    df = convertir_encabezados_a_mayusculas(df)
    
    columnas_eliminadas = []
    filas_eliminadas = 0
    
    if "FECHA_ANIO_MES" in df.columns:
        fecha_orden = convertir_fecha_anio_mes_a_orden(df["FECHA_ANIO_MES"])
        df = insertar_columna_despues(df, "FECHA_ANIO_MES", "FECHA_ORDEN_MES", fecha_orden)
        df, eliminadas = eliminar_columnas(df, ["FECHA_ANIO_MES"])
        columnas_eliminadas.extend(eliminadas)
    
    if "SEXO" in df.columns:
        df["SEXO"] = mapear_sexo_genero_binario(df["SEXO"]).astype("Int64")
        filas_antes = len(df)
        df = df[df["SEXO"].isin([0, 1])].copy()
        filas_eliminadas = filas_antes - len(df)
    
    if "EDAD_RANGO" in df.columns:
        df["EDAD_RANGO"] = mapear_edad_rango_ordinal(df["EDAD_RANGO"]).astype("Int64")
    
    if "EDAD" in df.columns:
        df["EDAD"] = escalar_edad_0_130(df["EDAD"])
    
    if "CAUSA_DEF" in df.columns:
        df["CAUSA_DEF_FREQ"] = frecuencia_absoluta_entera(df["CAUSA_DEF"])
    
    df, eliminadas = eliminar_columnas(df, ["LISTA_MEX", "ENT_OCURR"])
    columnas_eliminadas.extend(eliminadas)
    
    columnas_excluir_redundancia = ["ID_REGISTRO_DEF"]
    pares_pearson, sugeridas_pearson = detectar_redundancia_pearson(
        df, columna_objetivo=columna_objetivo, columnas_excluir=columnas_excluir_redundancia, umbral=umbral_redundancia
    )
    
    pares_chi2, sugeridas_chi2 = detectar_redundancia_chi2(
        df, columna_objetivo=columna_objetivo, columnas_excluir=columnas_excluir_redundancia, umbral_v=umbral_redundancia, max_unicos=20
    )
    
    columnas_redundantes = sorted((sugeridas_pearson | sugeridas_chi2) - {columna_objetivo})
    
    if eliminar_redundantes:
        df = df.drop(columns=columnas_redundantes, errors="ignore")
    
    df.to_csv(archivo_salida, index=False, encoding="utf-8-sig")
    
    print("##################################################")
    print("TRANSFORMACION Y REDUCCION DEFUNCIONES")
    print("##################################################\n")
    print("Archivo de salida:", archivo_salida)
    print("Filas eliminadas por SEXO no binario:", filas_eliminadas)
    print("Columnas eliminadas por regla:", columnas_eliminadas)
    print("Pares redundantes Pearson:", pares_pearson)
    print("Pares redundantes chi2:", pares_chi2)
    print("Columnas redundantes sugeridas:", columnas_redundantes)
    print("Eliminar redundantes:", eliminar_redundantes)
    print("Dimensiones finales:", df.shape)
    
    return ()
