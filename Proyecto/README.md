# Proyecto VIH/SIDA - Preprocesamiento para Ciencia de Datos

Proyecto escolar para integrar, perfilar, limpiar, deduplicar, transformar y analizar datos publicos de salud relacionados con VIH/SIDA en Ciudad de Mexico.

## Datos de entrada

Descargar las bases desde la carpeta de Drive:

```text
drive.google.com/qwerty
```

Colocar los CSV en:

```text
Bases de datos/
```

## Entorno local

Crear un entorno de Python e instalar dependencias:

```powershell
pip install -r requirements.txt
```

Librerias principales: `pandas`, `numpy`, `matplotlib`, `psycopg2`, `recordlinkage`, `scikit-learn`, `networkx`, `faiss-cpu`, `joblib` y `llama-cpp-python`.

## Configuracion del proyecto

Las rutas principales y los datos de conexion por omision estan en:

```text
code_python/config.py
```

Ese archivo concentra:

- carpeta de datos
- carpeta de salidas
- ruta del modelo LLM
- conexion local a PostgreSQL

## PostgreSQL

El proyecto espera una base local llamada:

```text
proyecto_preprocesamiento_CD_VIH
```

Credenciales por omision usadas por el codigo:

```text
PGHOST=localhost
PGPORT=5432
PGDATABASE=proyecto_preprocesamiento_CD_VIH
PGUSER=postgres
PGPASSWORD=deswa123
```

Si tu equipo usa otra contrasena o usuario, definir esas variables de entorno antes de ejecutar Python o ajustar `code_python/config.py`.

Crear tablas y vistas con:

```text
script_sql/00_crear_tablas_reproducible.sql
script_sql/01_crear_vistas_reproducible.sql
```

## Modelo LLM

Usar el modelo local:

```text
Llama-3.2-3B-Instruct-Q4_K_M.gguf
```

Colocarlo en:

```text
modelos/Llama-3.2-3B-Instruct-Q4_K_M.gguf
```

El modelo no se sube al repositorio por peso.

## Ejecucion

El archivo principal es:

```powershell
python main.py
```

`main.py` esta organizado por bloques comentables: combinacion, perfilado, limpieza, deduplicacion, transformacion, carga SQL, analisis, grafo/vectorial y preguntas con LLM. Activar solo las etapas necesarias.

## Salidas

Las salidas principales se generan en:

- `salidas/perfilado/`: imagenes de perfilado.
- `salidas/analisis/`: resumenes descriptivos, correlaciones y respuestas LLM.
- `salidas/grafo/`: grafo NetworkX en PKL, JSON, PNG y CSV de nodos/deltas.
- `salidas/vectorial/`: indice FAISS, corpus y metadatos para busqueda vectorial.

Mineria descriptiva conserva:

- `resumen_analisis_mineria.json`
- `resumen_por_periodo.csv`
- `resumen_por_sexo.csv`
- `resumen_por_grupo_edad.csv`
- `correlaciones_indicadores.csv`
- `correlaciones_indicadores.png`

Las 20 respuestas se guardan en:

```text
salidas/analisis/respuestas_20_preguntas.json
```
