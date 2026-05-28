########## CÓDIGO PARA EJECUTAR TODOS MIS CÓDIGOS DE FORMA MÁS CONTROLADA
from pathlib import Path
import runpy

ruta_proyecto_inicial = Path(__file__).resolve().parent

################ MENÚ DE OPCIONES #################

# 1. UNIFICAR BASES DE DATOS ORIGINALES  LISTO
# 2. PERFILADO DE LAS BASES DE DATOS   
# 3. LIMPIEZA DE LAS DB
# 4. DETECCIÓN DE DUPLICADOS DE LAS DB
# 5. POST PERFILADO DE LAS DB (PENDIENTE)
# 6. TRANSFORMACIÓN DE LAS DB
# 7. CARGA Y UPDATE DATOS A POSTGRESQL



############# IMPORT DE FUNCIONES DE OTROS CÓDIGOS ########
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

from code_python.consultas_llm import consultar_llm
from code_python.interpretador_llm import interpretar_llm

# # ############# Unificador de bases de datos ################
# combinar_vih()
# combinar_defunciones()
# combinar_consultas_hospital()

# # ################ Pre perfilado bases de datos ##################
# pre_perfilar_vih = ruta_proyecto_inicial / "code_python" / "perfilar_vih.py"
# pre_perfilar_defunciones = ruta_proyecto_inicial / "code_python" / "perfilar_defunciones.py"
# pre_perfilar_consultas_hospital = ruta_proyecto_inicial / "code_python" / "perfilar_consultas_hospital.py"

# runpy.run_path(str(pre_perfilar_vih), run_name="__main__")
# runpy.run_path(str(pre_perfilar_defunciones), run_name="__main__")
# runpy.run_path(str(pre_perfilar_consultas_hospital), run_name="__main__")

# # ############ Limpieza y estandarización #############

# limpieza_estandarizacion_vih()
# limpieza_estandarizacion_consultas_hospital()
# limpieza_estandarizacion_defunciones()

# deduplicar_vih()
# deduplicar_consultas_hospital()
# deduplicar_defunciones()

# transformar_reducir_vih()
# transformar_reducir_consultas_hospital()
# transformar_reducir_defunciones()

# cargar_a_sql()

# crear_grafo_metricas_mensuales()
# crear_corpus_vectorial_hgm_faiss()

pregunta = "Qué diferencias se observan por sexo en consultas, CD4, defunciones y porcentaje de pruebas reactivas a lo largo del periodo 2019–2023"
resultado = consultar_llm(pregunta)
interpretacion = interpretar_llm(pregunta, resultado)




