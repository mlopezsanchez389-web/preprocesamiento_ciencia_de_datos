from pathlib import Path
import pickle
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

# =========================================================
# CONFIGURACION GENERAL
# =========================================================

BASE_DIR = Path(__file__).resolve().parent
DATOS_DIR = BASE_DIR / "datos" / "vectorial"
RESULTADOS_DIR = BASE_DIR / "resultados" / "vectorial"

DATOS_DIR.mkdir(parents=True, exist_ok=True)
RESULTADOS_DIR.mkdir(parents=True, exist_ok=True)

ARCHIVO_INDICE = DATOS_DIR / "indice_vectorial_tfidf.pkl"

# =========================================================
# PREGUNTAS VECTORIALES
# =========================================================

PREGUNTAS_VECTORIALES = {
    11: "¿Qué combinación de cambios en consultas, valores de CD4 y porcentaje de pruebas reactivas permite anticipar periodos con mayor riesgo de incremento en defunciones por VIH/SIDA?",
    15: "¿La combinación de menor actividad en consultas y mayor proporción de casos con CD4 bajo permite predecir periodos con mayor presión clínica futura?",
    16: "¿Qué patrones temporales son más consistentes para anticipar si una caída en indicadores observados responde a reducción real del fenómeno o a subdetección?",
    20: "¿Qué escenarios temporales de recuperación en consultas y detección serían compatibles con una reducción esperada en severidad al diagnóstico y mortalidad por VIH/SIDA?"
}

EXPANSIONES = {
    11: "periodos mayor riesgo incremento defunciones vih cambios consultas cd4 porcentaje pruebas reactivas anticipar riesgo aumento mortalidad",
    15: "menor actividad consultas mayor proporcion casos cd4 bajo mayor presion clinica futura deteccion tardia severidad",
    16: "patrones temporales reduccion real subdeteccion caida indicadores observados pruebas consultas cd4 defunciones consistencia",
    20: "escenarios temporales recuperacion consultas deteccion reduccion esperada severidad diagnostico mortalidad vih"
}

# =========================================================
# FUNCIONES
# =========================================================

def cargar_indice():
    if not ARCHIVO_INDICE.exists():
        raise FileNotFoundError(
            f"No se encontró el índice vectorial en {ARCHIVO_INDICE}. "
            f"Ejecuta primero vectorial_preparacion.py"
        )

    with open(ARCHIVO_INDICE, "rb") as f:
        indice = pickle.load(f)
    return indice

def expandir_consulta(numero_pregunta: int) -> str:
    return PREGUNTAS_VECTORIALES[numero_pregunta] + " " + EXPANSIONES[numero_pregunta]

def ejecutar_busqueda_vectorial(numero_pregunta: int, top_k: int = 8) -> pd.DataFrame:
    indice = cargar_indice()
    vectorizer = indice["vectorizer"]
    matriz = indice["matriz"]
    documentos = indice["documentos"].copy()

    consulta = expandir_consulta(numero_pregunta)
    q = vectorizer.transform([consulta])

    similitudes = cosine_similarity(q, matriz).flatten()
    documentos["score_similitud"] = similitudes

    resultado = (
        documentos
        .sort_values("score_similitud", ascending=False)
        .head(top_k)
        .reset_index(drop=True)
    )
    return resultado

def resumir_resultado_vectorial(resultado: pd.DataFrame) -> pd.DataFrame:
    columnas = ["doc_id", "anio", "mes", "periodo", "score_similitud", "texto"]
    columnas_presentes = [c for c in columnas if c in resultado.columns]
    return resultado[columnas_presentes].copy()

def guardar_resultado(resultado: pd.DataFrame, numero_pregunta: int) -> Path:
    ruta_salida = RESULTADOS_DIR / f"resultado_pregunta_{numero_pregunta}_vectorial.csv"
    resultado.to_csv(ruta_salida, index=False, encoding="utf-8-sig")
    return ruta_salida

def mostrar_menu():
    print("##################################################")
    print("CONSULTAS VECTORIALES - AVANCE 5")
    print("##################################################\n")
    print("Preguntas disponibles:\n")
    for numero, texto in PREGUNTAS_VECTORIALES.items():
        print(f"{numero}: {texto}")
    print()

# =========================================================
# MAIN
# =========================================================

def main():
    mostrar_menu()
    numero_pregunta = int(input("Selecciona el numero de pregunta vectorial: ").strip())

    resultado = ejecutar_busqueda_vectorial(numero_pregunta, top_k=8)
    resultado = resumir_resultado_vectorial(resultado)

    print("\nPrimeros resultados recuperados:\n")
    print(resultado.head(8))
    print("\nDocumentos recuperados:", len(resultado))

    ruta_salida = guardar_resultado(resultado, numero_pregunta)
    print("Archivo guardado en:", ruta_salida)

if __name__ == "__main__":
    main()
