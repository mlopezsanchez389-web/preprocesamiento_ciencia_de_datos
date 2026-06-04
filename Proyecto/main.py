from pathlib import Path
import json
import runpy

from code_python.herramientas.combinador_vih import combinar_vih
from code_python.herramientas.combinador_defunciones import combinar_defunciones
from code_python.herramientas.combinador_consultas_hospital import combinar_consultas_hospital

from code_python.herramientas.limpieza_estandarizacion_vih import limpieza_estandarizacion_vih
from code_python.herramientas.limpieza_estandarizacion_consultas_hospital import limpieza_estandarizacion_consultas_hospital
from code_python.herramientas.limpieza_estandarizacion_defunciones import limpieza_estandarizacion_defunciones

from code_python.deduplicar_vih import deduplicar_vih
from code_python.deduplicar_consultas_hospital import deduplicar_consultas_hospital
from code_python.deduplicar_defunciones import deduplicar_defunciones

from code_python.herramientas.Transformacion_y_reduccion_de_consultas_hospital import transformar_reducir_consultas_hospital
from code_python.herramientas.Transformacion_y_reduccion_de_defunciones import transformar_reducir_defunciones
from code_python.herramientas.Transformacion_y_reduccion_de_vih import transformar_reducir_vih

from code_python.cargar_sql import cargar_a_sql
from code_python.crear_grafo_networkx import crear_grafo_metricas_mensuales
from code_python.crear_corpus_vectorial import crear_corpus_vectorial_hgm_faiss
from code_python.analisis_mineria_descriptiva import ejecutar_analisis_mineria_descriptiva
from code_python.consultas_llm import consultar_llm
from code_python.interpretador_llm import interpretar_llm
from code_python.config import RUTA_PROYECTO, SALIDA_ANALISIS


ruta_proyecto = RUTA_PROYECTO
ruta_salidas = SALIDA_ANALISIS
ruta_respuestas = ruta_salidas / "respuestas_20_preguntas.json"


preguntas = [
    "Como cambiaron entre 2019 y 2023 las consultas relacionadas con VIH en Ciudad de Mexico y como se compara esa tendencia con la de las defunciones por VIH/SIDA en el mismo periodo?",
    "Como vario entre 2019 y 2023 la severidad clinica al diagnostico, medida mediante CD4, y como se relaciona temporalmente con los cambios en consultas y defunciones?",
    "Como cambio entre 2019 y 2023 el porcentaje anual de pruebas reactivas y como se comportaron, en ese mismo periodo, las consultas y las defunciones asociadas a VIH/SIDA?",
    "Que diferencias se observan por sexo en consultas, CD4, defunciones y porcentaje de pruebas reactivas a lo largo del periodo 2019-2023?",
    "Que diferencias se observan por grupos de edad en consultas, severidad al diagnostico y defunciones por VIH/SIDA durante el periodo de estudio?",
    "Como se comportaron antes, durante y despues de la pandemia las consultas por VIH, los valores de CD4, las defunciones y el porcentaje de pruebas reactivas?",
    "En que periodos se observa una disminucion simultanea o divergente entre consultas, porcentaje de pruebas reactivas y defunciones por VIH/SIDA?",
    "Como cambio la proporcion de consultas de primera vez frente a subsecuentes entre 2019 y 2023, y como se relaciona con la severidad clinica al diagnostico y con la mortalidad?",
    "Que patron temporal muestran los casos con CD4 sugestivo de deteccion tardia y como coincide con los cambios en consultas y defunciones?",
    "Que anios del periodo 2019-2023 presentan la mayor discrepancia entre porcentaje de pruebas reactivas, demanda de atencion y mortalidad por VIH/SIDA?",
    "Que combinacion de cambios en consultas, valores de CD4 y porcentaje de pruebas reactivas permite anticipar periodos con mayor riesgo de incremento en defunciones por VIH/SIDA?",
    "La disminucion en consultas y en porcentaje de pruebas reactivas permite predecir un aumento posterior en casos con CD4 bajo, consistente con deteccion tardia?",
    "Que perfiles de sexo y edad presentan mayor probabilidad de concentrar diagnosticos con mayor severidad clinica en periodos de menor deteccion aparente?",
    "Que variaciones en el porcentaje anual de pruebas reactivas permiten anticipar cambios posteriores en la demanda de atencion clinica por VIH?",
    "La combinacion de menor actividad en consultas y mayor proporcion de casos con CD4 bajo permite predecir periodos con mayor presion clinica futura?",
    "Que patrones temporales son mas consistentes para anticipar si una caida en indicadores observados responde a reduccion real del fenomeno o a subdeteccion?",
    "Que grupos de edad y sexo presentan mayor probabilidad de mostrar un patron de deteccion tardia cuando disminuyen las consultas o cambia la proporcion de pruebas reactivas?",
    "Los cambios observados en un anio del porcentaje de pruebas reactivas permiten anticipar variaciones en las defunciones por VIH/SIDA en el anio siguiente?",
    "Que combinacion de indicadores temporales permite identificar periodos con mayor probabilidad de desacople entre menor deteccion aparente y persistencia de desenlaces graves?",
    "Que escenarios temporales de recuperacion en consultas y deteccion serian compatibles con una reduccion esperada en severidad al diagnostico y mortalidad por VIH/SIDA?",
]


def guardar_respuesta(registro):
    respuestas = json.loads(ruta_respuestas.read_text(encoding="utf-8"))
    respuestas.append(registro)
    ruta_respuestas.write_text(json.dumps(respuestas, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


print("Inicio del flujo del proyecto.")

# combinar_vih()
# combinar_defunciones()
# combinar_consultas_hospital()

# runpy.run_path(str(ruta_proyecto / "code_python" / "perfilar_vih.py"), run_name="__main__")
# runpy.run_path(str(ruta_proyecto / "code_python" / "perfilar_defunciones.py"), run_name="__main__")
# runpy.run_path(str(ruta_proyecto / "code_python" / "perfilar_consultas_hospital.py"), run_name="__main__")

# limpieza_estandarizacion_vih()
# limpieza_estandarizacion_consultas_hospital()
# limpieza_estandarizacion_defunciones()

# deduplicar_vih()
# deduplicar_consultas_hospital()
# deduplicar_defunciones()

# runpy.run_path(str(ruta_proyecto / "code_python" / "perfilar_vih_limpio_sin_duplicados.py"), run_name="__main__")
# runpy.run_path(str(ruta_proyecto / "code_python" / "perfilar_defunciones_limpio_sin_duplicados.py"), run_name="__main__")
# runpy.run_path(str(ruta_proyecto / "code_python" / "perfilar_consultas_hospital_limpio_sin_duplicados.py"), run_name="__main__")

# transformar_reducir_vih()
# transformar_reducir_consultas_hospital()
# transformar_reducir_defunciones()

# cargar_a_sql()

# ejecutar_analisis_mineria_descriptiva()

# crear_grafo_metricas_mensuales()
# crear_corpus_vectorial_hgm_faiss()

# ruta_salidas.mkdir(exist_ok=True)
# ruta_respuestas.write_text("[]", encoding="utf-8")

# for numero, pregunta in enumerate(preguntas, start=1):
#     print(f"\nPregunta {numero}/20")
#     print(pregunta)
#
#     resultado = None
#     interpretacion = None
#     error_pregunta = None
#
#     try:
#         resultado = consultar_llm(pregunta)
#
#         if resultado.get("backend") == "ERROR_JSON":
#             raise ValueError(resultado.get("error", "Error al leer JSON del LLM."))
#
#         interpretacion = interpretar_llm(pregunta, resultado)
#     except Exception as error:
#         error_pregunta = str(error)
#         print(f"Error en pregunta {numero}: {error_pregunta}")
#
#     guardar_respuesta({
#         "numero": numero,
#         "pregunta": pregunta,
#         "resultado": resultado,
#         "interpretacion": interpretacion,
#         "error": error_pregunta
#     })
#
# print(f"\nRespuestas guardadas en: {ruta_respuestas}")
print("Flujo terminado.")
