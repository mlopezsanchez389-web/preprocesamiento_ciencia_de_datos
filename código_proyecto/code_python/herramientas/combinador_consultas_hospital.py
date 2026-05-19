import pandas as pd
from pathlib import Path

def combinar_consultas_hospital ():
    
    ruta_proyecto = Path(__file__).resolve().parents[2]        
    ruta = Path("Bases de datos")
    archivos = [
        "CONSULTAS_OTORGADAS_2019.csv",
        "CONSULTAS_OTORGADAS_2020.csv",
        "CONSULTAS_OTORGADAS_2021.csv",
        "CONSULTAS_OTORGADAS_2022.csv",
        "CONSULTAS_OTORGADAS_2023.csv"  
        ]
    ruta = ruta_proyecto/ruta

    RENOMBRAR_COLUMNAS = True
    
    NUEVOS_NOMBRES = {
        "CONSULTAS_OTORGADAS_2019.csv": [
            "FECHA","TIPO_CONSULTA","CLAVE_PROCEDENCIA","PROCEDENCIA","CLAVE_SEXO","SEXO","EDAD","CLAVE_UNIDAD","UNIDAD","CLAVE_ESPECIALIDAD","ESPECIALIDAD","CODIGO","DESCRIPCION_DIAGNOSTICO"
        ],
        "CONSULTAS_OTORGADAS_2020.csv": [
            "FECHA","TIPO_CONSULTA","PROCEDENCIA","SEXO","EDAD","UNIDAD","ESPECIALIDAD","CODIGO","DESCRIPCION_DIAGNOSTICO"
        ],
        "CONSULTAS_OTORGADAS_2021.csv": [
            "FECHA","TIPO_CONSULTA","PROCEDENCIA","SEXO","EDAD","UNIDAD","ESPECIALIDAD","CODIGO","DESCRIPCION_DIAGNOSTICO"
        ],
        "CONSULTAS_OTORGADAS_2022.csv": [
            "FECHA","TIPO_CONSULTA","PROCEDENCIA","SEXO","EDAD","UNIDAD","ESPECIALIDAD","CODIGO","DESCRIPCION_DIAGNOSTICO"
        ],
        "CONSULTAS_OTORGADAS_2023.csv": [
            "FECHA", "TIPO_CONSULTA","PROCEDENCIA","SEXO","EDAD","UNIDAD","ESPECIALIDAD","CODIGO","DESCRIPCION_DIAGNOSTICO"
        ],     
    }
    
    
    def renombrar(df: pd.DataFrame, archivo: str) -> pd.DataFrame:
        nombres_nuevos = NUEVOS_NOMBRES[archivo]
    
        if len(nombres_nuevos) != len(df.columns):
            raise ValueError(
                f"El archivo {archivo} tiene {len(df.columns)} columnas, "
                f"pero se definieron {len(nombres_nuevos)} nombres nuevos."
            )
    
        df = df.copy()
        df.columns = nombres_nuevos
        return df
    
    columnas_por_archivo = {}
    dfs = []
    filas_total = 0
    for archivo in archivos:
        ruta_completa = ruta / archivo
    
        # Leer archivo completo
        df = pd.read_csv(ruta_completa, encoding="latin-1", sep=",", low_memory=False)
        filas_total=filas_total+len(df)
    
        # Renombrar columnas si esta habilitado
        if RENOMBRAR_COLUMNAS == True:
            df = renombrar(df, archivo)
    
        # Convertir espacios vacios en NA y eliminar filas totalmente vacias
        df = df.replace(r'^\s*$', pd.NA, regex=True).dropna(how="all")
    
        # Filtrar solo CDMX (ENT_OCURR == 9)
        if "PROCEDENCIA" in df.columns:
            df = df[df["PROCEDENCIA"] == "CIUDAD DE MEXICO"].copy()
        else:
            print(f"[AVISO] El archivo {archivo} no tiene la columna PROCEDENCIA y no se filtró.")
    
        columnas_por_archivo[archivo] = set(df.columns)
        dfs.append(df)
    
    # Obtener columnas comunes
    columnas_comunes = set(columnas_por_archivo[archivos[0]])
    for archivo in archivos[1:]:
        columnas_comunes = columnas_comunes.intersection(columnas_por_archivo[archivo])
    
    # Conservar orden segun el primer dataframe
    columnas_comunes_ordenadas = [col for col in dfs[0].columns if col in columnas_comunes]
    print("############ CONSULTAS HOSPITAL GRA. DE MÉXICO: FUSIÓN Y FILTRADO A CDMX ############\n")

    print("Estas columnas se repiten en todos los CSV:")
    print(columnas_comunes_ordenadas)
    print("\n" + "-" * 60 + "\n")
    
    columnas_excluidas_totales = set()
    
    for archivo in archivos:
        columnas_no_comunes = columnas_por_archivo[archivo] - columnas_comunes
        columnas_excluidas_totales.update(columnas_no_comunes)
    
        print(f"Este CSV {archivo} tiene estas columnas que no se repiten en todos los CSV:")
        print(sorted(columnas_no_comunes))
        print()
    
    dfs_comunes = []
    for df in dfs:
        df_comun = df[columnas_comunes_ordenadas].copy()
        dfs_comunes.append(df_comun)
        
    
    df_union_comunes = pd.concat(dfs_comunes, ignore_index=True, sort=False)
    
    salida_comunes = ruta / "consultas_HGM_cdmx_2019_2023.csv"
    df_union_comunes.to_csv(salida_comunes, index=False, encoding="utf-8-sig")
    porcentaje_reduccion= len(df_union_comunes)*100/filas_total
    
    print(f"Guardada en: {salida_comunes}")
    print(f"Total registros antes de filtrado: {filas_total}")
    print(f"Total registros resultantes: {len(df_union_comunes)}")
    print(f"Porcentaje resultante tras filtrado: {porcentaje_reduccion}\n" )
    print(f"Cantidad de columnas mantenidas: {len(df_union_comunes.columns)}")
    print("Cantidad total de columnas excluidas:", len(columnas_excluidas_totales))
    
    return ()