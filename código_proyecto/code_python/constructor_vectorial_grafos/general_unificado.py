from pathlib import Path

from sql_unificado import ejecutar_pregunta_sql, guardar_resultado as guardar_resultado_sql
from grafo_unificado import (
    ejecutar_pregunta_grafo,
    guardar_resultado_csv as guardar_resultado_grafo_csv,
    cargar_grafo,
    construir_subgrafo_desde_resultado,
    plotear_subgrafo
)
from vectorial_unificado import (
    ejecutar_busqueda_vectorial,
    resumir_resultado_vectorial,
    guardar_resultado as guardar_resultado_vectorial
)

# =========================================================
# RUTEO GENERAL
# =========================================================

RUTEO_GENERAL = {
    1: "sql",
    2: "grafo",
    3: "sql",
    4: "sql",
    5: "sql",
    6: "sql",
    7: "grafo",
    8: "grafo",
    9: "sql",
    10: "grafo",
    11: "vectorial",
    12: "sql",
    13: "sql",
    14: "sql",
    15: "vectorial",
    16: "vectorial",
    17: "sql",
    18: "sql",
    19: "grafo",
    20: "vectorial"
}

PREGUNTAS = {
    1: "Consultas relacionadas con VIH vs defunciones",
    2: "Severidad clínica al diagnóstico y relación con consultas y defunciones",
    3: "Pruebas reactivas vs consultas y defunciones",
    4: "Diferencias por sexo",
    5: "Diferencias por grupos de edad",
    6: "Antes, durante y después de pandemia",
    7: "Disminución simultánea o divergente",
    8: "Primera vez vs subsecuentes y relación con severidad y mortalidad",
    9: "Patrón temporal de CD4 sugestivo de detección tardía",
    10: "Años con mayor discrepancia entre pruebas, atención y mortalidad",
    11: "Cambios que anticipan mayor riesgo de defunciones",
    12: "Disminución en consultas y pruebas vs CD4 bajo",
    13: "Perfiles de sexo y edad con mayor severidad clínica",
    14: "Variaciones en pruebas reactivas y demanda clínica",
    15: "Menor actividad y mayor CD4 bajo como presión clínica futura",
    16: "Reducción real o subdetección",
    17: "Grupos de edad y sexo con patrón de detección tardía",
    18: "Pruebas reactivas y defunciones al año siguiente",
    19: "Indicadores con desacople entre detección y desenlaces graves",
    20: "Escenarios de recuperación compatibles con menor severidad y mortalidad"
}

# =========================================================
# MENU
# =========================================================

def mostrar_menu():
    print("##################################################")
    print("ORQUESTADOR GENERAL UNIFICADO - AVANCE 5")
    print("##################################################\n")
    print("Preguntas disponibles:\n")

    for numero, texto in PREGUNTAS.items():
        backend = RUTEO_GENERAL[numero]
        print(f"{numero}: {texto} [{backend}]")

    print()

# =========================================================
# EJECUCION POR BACKEND
# =========================================================

def ejecutar_y_guardar(numero_pregunta: int):
    backend = RUTEO_GENERAL[numero_pregunta]

    if backend == "sql":
        resultado = ejecutar_pregunta_sql(numero_pregunta)
        ruta_csv = guardar_resultado_sql(resultado, numero_pregunta)
        return backend, resultado, {"csv": ruta_csv}

    elif backend == "grafo":
        resultado = ejecutar_pregunta_grafo(numero_pregunta)
        ruta_csv = guardar_resultado_grafo_csv(resultado, numero_pregunta)

        G = cargar_grafo()
        subG = construir_subgrafo_desde_resultado(G, resultado)
        ruta_img = plotear_subgrafo(subG, numero_pregunta)

        return backend, resultado, {
            "csv": ruta_csv,
            "imagen": ruta_img,
            "nodos_subgrafo": subG.number_of_nodes(),
            "aristas_subgrafo": subG.number_of_edges()
        }

    elif backend == "vectorial":
        resultado = ejecutar_busqueda_vectorial(numero_pregunta, top_k=8)
        resultado = resumir_resultado_vectorial(resultado)
        ruta_csv = guardar_resultado_vectorial(resultado, numero_pregunta)
        return backend, resultado, {"csv": ruta_csv}

    else:
        raise ValueError(f"Backend no reconocido: {backend}")

# =========================================================
# MAIN
# =========================================================

def main():
    mostrar_menu()
    numero_pregunta = int(input("Selecciona el número de pregunta: ").strip())

    backend, resultado, rutas = ejecutar_y_guardar(numero_pregunta)

    print(f"\nBackend utilizado: {backend}")
    print("\nPrimeros 20 registros:\n")
    print(resultado.head(20))
    print("\nFilas devueltas:", len(resultado))

    print("\nArchivos generados:")
    for clave, valor in rutas.items():
        print(f"{clave}: {valor}")

if __name__ == "__main__":
    main()
