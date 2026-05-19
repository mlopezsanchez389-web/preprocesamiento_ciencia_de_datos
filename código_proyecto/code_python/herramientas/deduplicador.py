import pandas as pd
import recordlinkage
from recordlinkage.preprocessing import clean
from pathlib import Path
pd.set_option("display.max_rows", None)
pd.set_option("display.max_columns", None)
pd.set_option("display.expand_frame_repr", False)


ruta_proyecto = Path(__file__).resolve().parents[2]

ruta = "Bases de datos"
ruta = ruta_proyecto / ruta

def cargar_y_limpiar(
    archivo_csv: str,
    variable_id: str | None,
    comparaciones: list,
    encoding: str = "latin-1",
    sep: str = ","
) -> pd.DataFrame:
    df = pd.read_csv(archivo_csv, encoding=encoding, sep=sep, low_memory=False)
    df_clean = df.copy()

    if variable_id is not None and variable_id in df_clean.columns:
        df_clean = df_clean.set_index(variable_id)
    else:
        df_clean = df_clean.reset_index(drop=True)
        df_clean.index.name = "ID_TEMP"

    return df_clean

def generar_pares(df_clean: pd.DataFrame, columnas_blocking: list) -> pd.MultiIndex:
    indexer = recordlinkage.Index()
    indexer.block(columnas_blocking)
    return indexer.index(df_clean)

def preparar_dataframe_para_comparacion(df_clean: pd.DataFrame, comparaciones: list) -> pd.DataFrame:
    df_temp = df_clean.copy()

    for config in comparaciones:
        columna = config["columna"]
        tipo = config["tipo"]

        if tipo == "string":
            df_temp[columna] = clean(df_temp[columna], strip_accents="unicode")
        elif tipo == "numeric":
            df_temp[columna] = pd.to_numeric(df_temp[columna], errors="coerce")
        elif tipo == "date":
            df_temp[columna] = pd.to_datetime(df_temp[columna], errors="coerce", dayfirst=True)
        elif tipo == "exact":
            pass
        else:
            raise ValueError(f"Tipo de comparación no soportado: {tipo}")

    return df_temp

def construir_comparador(comparaciones: list) -> recordlinkage.Compare:
    compare = recordlinkage.Compare()

    for config in comparaciones:
        columna = config["columna"]
        tipo = config["tipo"]
        label = config.get("label", columna + "_ok")

        if tipo == "string":
            metodo = config.get("metodo", "jarowinkler")
            compare.string(columna, columna, method=metodo, label=label)
        elif tipo == "exact":
            compare.exact(columna, columna, label=label)
        elif tipo == "numeric":
            metodo = config.get("metodo", "linear")
            offset = config.get("offset", 0)
            scale = config.get("scale", 1)
            origin = config.get("origin", 0)

            compare.numeric(
            columna,
            columna,
            method=metodo,
            offset=offset,
            scale=scale,
            origin=origin,
            label=label
            )
        
        elif tipo == "date":
            pass
        else:
            raise ValueError(f"Tipo de comparación no soportado: {tipo}")

    return compare

def detectar_duplicados(
    df_clean: pd.DataFrame,
    pairs: pd.MultiIndex,
    comparaciones: list,
    umbral
) -> dict:
    df_compare = preparar_dataframe_para_comparacion(df_clean, comparaciones)
    compare = construir_comparador(comparaciones)
    features = compare.compute(pairs, df_compare)

    left_idx = features.index.get_level_values(0)
    right_idx = features.index.get_level_values(1)

    for config in comparaciones:
        if config["tipo"] == "date":
            columna = config["columna"]
            label = config.get("label", columna + "_ok")
            margen_dias = config.get("margen_dias", 0)

            fechas_izq = df_compare.loc[left_idx, columna].to_numpy()
            fechas_der = df_compare.loc[right_idx, columna].to_numpy()

            diferencia_dias = pd.Series((fechas_izq - fechas_der)).dt.days.abs().to_numpy()
            features[label] = (diferencia_dias <= margen_dias).astype(int)

    matches = features[features.sum(axis=1) >= umbral]
    links = matches.index

    if len(links) > 0:
        cc = recordlinkage.ConnectedComponents()
        componentes = list(cc.compute(links))
    else:
        componentes = []

    sobrantes = 0
    for comp_i in componentes:
        ids = (
            pd.Index(comp_i.get_level_values(0))
            .union(comp_i.get_level_values(1))
            .unique()
        )
        sobrantes += (len(ids) - 1)

    registros_unicos = len(df_clean) - sobrantes

    del df_compare
    del features
    del matches

    return {
        "total_registros": len(df_clean),
        "pares_candidatos": len(pairs),
        "pares_match": len(links),
        "sobrantes": sobrantes,
        "registros_unicos": registros_unicos,
        "links": links,
        "componentes": componentes,
    }

def generar_dataframe_sin_duplicados(df_clean: pd.DataFrame, componentes: list) -> pd.DataFrame:
    if len(componentes) == 0:
        return df_clean.reset_index().copy()

    ids_representantes = set()
    ids_en_componentes = set()

    for comp_i in componentes:
        ids = (
            pd.Index(comp_i.get_level_values(0))
            .union(comp_i.get_level_values(1))
            .unique()
        )
        ids_lista = list(ids)
        ids_representantes.add(min(ids_lista))
        ids_en_componentes.update(ids_lista)

    ids_sin_duplicados = set(df_clean.index) - ids_en_componentes
    ids_conservar = ids_representantes.union(ids_sin_duplicados)

    df_sin_dup = df_clean.loc[df_clean.index.isin(ids_conservar)].copy()
    df_sin_dup = df_sin_dup.reset_index()

    return df_sin_dup

def exportar_resultados(
    archivo_original: str,
    df_sin_dup: pd.DataFrame,
    encoding: str = "latin-1"
) -> None:
    archivo_sin_dup = str(archivo_original).replace(".csv", "_sin_duplicados.csv")
    df_sin_dup.to_csv(archivo_sin_dup, index=False, encoding=encoding)
    print("Archivo sin duplicados guardado en:", archivo_sin_dup)

def mostrar_resultados(df_clean: pd.DataFrame, res: dict, comparaciones: list, cantidad_muestra: int = 5) -> None:
    print("##################################################\n")
    print("Detector de duplicados")
    print("##################################################\n")

    print("Total de registros:", res["total_registros"])
    print("Pares candidatos identificados:", res["pares_candidatos"])
    print("Pares coincidentes:", res["pares_match"])
    print("Registros sobrantes o duplicados:", res["sobrantes"])
    print("Registros únicos:", res["registros_unicos"])
    print("\n##################################################\n")

    if len(res["links"]) == 0:
        return

    print(f"Muestra de los primeros {cantidad_muestra} pares coincidentes:\n")

    columnas_mostrar = [config["columna"] for config in comparaciones]

    for (i, j) in list(res["links"][:cantidad_muestra]):
        print("Par", (i, j))
        print("   Registro A:")
        for col in columnas_mostrar:
            print("      ", col, "=", df_clean.loc[i, col])
        print("   Registro B:")
        for col in columnas_mostrar:
            print("      ", col, "=", df_clean.loc[j, col])
        print()

def ejecutar_deduplicacion(
    archivo: str,
    encoding_archivo: str,
    sep_archivo: str,
    variable_id: str | None,
    columnas_blocking: list,
    umbral: float,
    comparaciones: list
) -> None:
    df_clean = cargar_y_limpiar(
        archivo_csv=archivo,
        variable_id=variable_id,
        comparaciones=comparaciones,
        encoding=encoding_archivo,
        sep=sep_archivo
    )

    pairs = generar_pares(df_clean, columnas_blocking=columnas_blocking)

    res = detectar_duplicados(
        df_clean=df_clean,
        pairs=pairs,
        comparaciones=comparaciones,
        umbral=umbral
    )

    mostrar_resultados(df_clean, res, comparaciones, cantidad_muestra=5)

    df_sin_dup = generar_dataframe_sin_duplicados(df_clean, res["componentes"])

    exportar_resultados(
        archivo_original=archivo,
        df_sin_dup=df_sin_dup,
        encoding=encoding_archivo
    )
