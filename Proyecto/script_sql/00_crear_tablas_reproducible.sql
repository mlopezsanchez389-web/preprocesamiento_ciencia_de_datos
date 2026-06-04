-- Script reproducible para crear las tablas base del proyecto.
-- Ejecutar primero en la base: proyecto_preprocesamiento_CD_VIH
-- Despues cargar CSV transformados con code_python/cargar_sql.py.

DROP VIEW IF EXISTS vw_metricas_mensuales_integradas_grupo_edad CASCADE;
DROP VIEW IF EXISTS vw_metricas_mensuales_integradas_sexo CASCADE;
DROP VIEW IF EXISTS vw_metricas_mensuales_integradas CASCADE;
DROP VIEW IF EXISTS vw_hgm_vector_cie_mensual CASCADE;
DROP VIEW IF EXISTS vw_pruebas_reactivas_mensual CASCADE;
DROP VIEW IF EXISTS vw_consultas_hgm_mensual CASCADE;
DROP VIEW IF EXISTS vw_vih_red_mensual CASCADE;
DROP VIEW IF EXISTS vw_defunciones_mensual CASCADE;
DROP VIEW IF EXISTS vw_calendario_mensual CASCADE;

DROP TABLE IF EXISTS consultas_hgm CASCADE;
DROP TABLE IF EXISTS vih_red CASCADE;
DROP TABLE IF EXISTS defunciones CASCADE;
DROP TABLE IF EXISTS pruebas_reactivas_cec CASCADE;

CREATE TABLE consultas_hgm (
    id_registro integer,
    fecha date,
    fecha_orden_mes integer,
    tipo_consulta text,
    sexo integer,
    edad double precision,
    especialidad text,
    codigo text,
    descripcion_diagnostico text,
    vih_flag integer,
    codigo_freq integer,
    especialidad_freq integer
);

CREATE TABLE vih_red (
    id_muestra text,
    fecha_toma date,
    fecha_orden_mes integer,
    sexo integer,
    genero integer,
    edad double precision,
    municipio integer,
    seguridad_social integer,
    cv double precision,
    cd4_a double precision,
    vih_tardio_flag integer
);

CREATE TABLE defunciones (
    id_registro_def integer,
    fecha_ocurr date,
    fecha_orden_mes integer,
    mes_ocurr integer,
    causa_def text,
    sexo integer,
    edad double precision,
    ent_resid integer,
    fecha_nacim text,
    ent_regis integer,
    mun_resid integer,
    mun_ocurr integer,
    lugar_ocur integer,
    asist_medi integer,
    derechohab integer,
    vih_flag integer,
    causa_def_freq integer
);

CREATE TABLE pruebas_reactivas_cec (
    anio integer PRIMARY KEY,
    pruebas_reactivas integer,
    pct_reactivas_consejeria double precision,
    pct_reactivas_otros_programas double precision
);

