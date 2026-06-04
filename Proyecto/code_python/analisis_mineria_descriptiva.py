from pathlib import Path
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import psycopg2

from code_python.config import DB_CONFIG, SALIDA_ANALISIS


def ejecutar_analisis_mineria_descriptiva():
    ruta_salida = SALIDA_ANALISIS
    ruta_salida.mkdir(exist_ok=True)

    conn = psycopg2.connect(**DB_CONFIG)

    df_mensual = pd.read_sql_query("""
        SELECT
            fecha_orden_mes, anio, mes, periodo,
            consultas_vih, proporcion_consultas_vih,
            muestras_total, cd4_promedio,
            casos_cd4_bajo, proporcion_cd4_bajo,
            defunciones_vih, proporcion_defunciones_vih,
            pruebas_reactivas,
            pct_reactivas_consejeria,
            pct_reactivas_otros_programas
        FROM vw_metricas_mensuales_integradas
        ORDER BY fecha_orden_mes;
    """, conn)

    df_periodo = pd.read_sql_query("""
        SELECT
            periodo,
            SUM(consultas_vih) AS consultas_vih,
            AVG(cd4_promedio) AS cd4_promedio,
            SUM(casos_cd4_bajo) AS casos_cd4_bajo,
            SUM(defunciones_vih) AS defunciones_vih,
            AVG(pct_reactivas_consejeria) AS pct_reactivas_consejeria_promedio
        FROM vw_metricas_mensuales_integradas
        GROUP BY periodo
        ORDER BY periodo;
    """, conn)

    df_sexo = pd.read_sql_query("""
        SELECT
            sexo_etiqueta,
            SUM(consultas_vih) AS consultas_vih,
            AVG(cd4_promedio) AS cd4_promedio,
            SUM(casos_cd4_bajo) AS casos_cd4_bajo,
            SUM(defunciones_vih) AS defunciones_vih
        FROM vw_metricas_mensuales_integradas_sexo
        GROUP BY sexo_etiqueta
        ORDER BY sexo_etiqueta;
    """, conn)

    df_edad = pd.read_sql_query("""
        SELECT
            grupo_edad,
            SUM(consultas_vih) AS consultas_vih,
            AVG(cd4_promedio) AS cd4_promedio,
            SUM(casos_cd4_bajo) AS casos_cd4_bajo,
            SUM(defunciones_vih) AS defunciones_vih
        FROM vw_metricas_mensuales_integradas_grupo_edad
        GROUP BY grupo_edad, orden_grupo_edad
        ORDER BY orden_grupo_edad;
    """, conn)

    conn.close()

    columnas = [
        "consultas_vih",
        "proporcion_consultas_vih",
        "muestras_total",
        "cd4_promedio",
        "casos_cd4_bajo",
        "proporcion_cd4_bajo",
        "defunciones_vih",
        "proporcion_defunciones_vih",
        "pruebas_reactivas",
        "pct_reactivas_consejeria",
        "pct_reactivas_otros_programas",
    ]

    datos = df_mensual[columnas].apply(pd.to_numeric, errors="coerce")
    correlaciones = datos.corr(method="pearson").round(4)

    correlaciones.to_csv(ruta_salida / "correlaciones_indicadores.csv", encoding="utf-8-sig")
    df_periodo.to_csv(ruta_salida / "resumen_por_periodo.csv", index=False, encoding="utf-8-sig")
    df_sexo.to_csv(ruta_salida / "resumen_por_sexo.csv", index=False, encoding="utf-8-sig")
    df_edad.to_csv(ruta_salida / "resumen_por_grupo_edad.csv", index=False, encoding="utf-8-sig")

    plt.figure(figsize=(9, 7))
    plt.imshow(correlaciones, cmap="coolwarm", vmin=-1, vmax=1)
    plt.colorbar(label="correlacion")
    plt.xticks(range(len(correlaciones.columns)), correlaciones.columns, rotation=45, ha="right")
    plt.yticks(range(len(correlaciones.index)), correlaciones.index)
    plt.title("Correlacion entre indicadores mensuales")
    plt.tight_layout()
    plt.savefig(ruta_salida / "correlaciones_indicadores.png", dpi=180)
    plt.close()

    resumen = {
        "filas_mensuales": len(df_mensual),
        "columnas_usadas": columnas,
        "correlaciones": correlaciones.to_dict(),
        "resumen_periodo": df_periodo.to_dict(orient="records"),
        "resumen_sexo": df_sexo.to_dict(orient="records"),
        "resumen_edad": df_edad.to_dict(orient="records"),
    }

    with open(ruta_salida / "resumen_analisis_mineria.json", "w", encoding="utf-8") as f:
        json.dump(resumen, f, ensure_ascii=False, indent=2, default=str)

    print("Analisis descriptivo generado.")
    print(f"Meses analizados: {len(df_mensual)}")
    print(f"Salida: {ruta_salida}")

    return resumen


if __name__ == "__main__":
    ejecutar_analisis_mineria_descriptiva()
