import pandas as pd
from pathlib import Path

def combinar_vih ():
    ruta_proyecto = Path(__file__).resolve().parents[2]
    
    
    archivo =   "vih_red_completa.csv"
    ruta = "Bases de datos"
    ruta = ruta_proyecto / ruta
    
    df = pd.read_csv(ruta/archivo, encoding="latin-1", sep=",", low_memory=False)
    
    long_antes=len(df)
    # Convertir espacios vacios en NA y eliminar filas totalmente vacias
    df = df.replace(r'^\s*$', pd.NA, regex=True).dropna(how="all")
    
    
    if "estado" in df.columns:
        df = df[df["estado"] == "Ciudad de Mexico"].copy()
    
    
    salida_comunes = ruta / "vih_red_completa_cdmx_2019_2023.csv"
    df.to_csv(salida_comunes, index=False, encoding="utf-8-sig")
    long_despues=len(df)
    
    porcentaje_reducc=long_despues*100/long_antes
    
    print("############ VIH RED CONAHCYT: FUSIÓN Y FILTRADO A CDMX ############\n")
    
    print(f"Archivo original: {ruta}/ {archivo}\n")
    print(f"Archivo generado: {salida_comunes}\n")
    
    print(f"Porcentaje de registros tras filtrado a CDMX: {porcentaje_reducc:.2f} %")

    return ()