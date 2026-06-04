-- Script reproducible para crear las vistas usadas por SQL, NetworkX y FAISS.
-- Ejecutar despues de crear tablas y cargar datos transformados.

DROP VIEW IF EXISTS vw_metricas_mensuales_integradas_grupo_edad CASCADE;
DROP VIEW IF EXISTS vw_metricas_mensuales_integradas_sexo CASCADE;
DROP VIEW IF EXISTS vw_metricas_mensuales_integradas CASCADE;
DROP VIEW IF EXISTS vw_hgm_vector_cie_mensual CASCADE;
DROP VIEW IF EXISTS vw_pruebas_reactivas_mensual CASCADE;
DROP VIEW IF EXISTS vw_consultas_hgm_mensual CASCADE;
DROP VIEW IF EXISTS vw_vih_red_mensual CASCADE;
DROP VIEW IF EXISTS vw_defunciones_mensual CASCADE;
DROP VIEW IF EXISTS vw_calendario_mensual CASCADE;

CREATE VIEW vw_calendario_mensual AS
SELECT
    (EXTRACT(YEAR FROM gs)::integer * 12 + EXTRACT(MONTH FROM gs)::integer) AS fecha_orden_mes,
    EXTRACT(YEAR FROM gs)::integer AS anio,
    EXTRACT(MONTH FROM gs)::integer AS mes,
    gs::date AS fecha_mes
FROM generate_series(date '2019-01-01', date '2023-12-01', interval '1 month') AS gs;

CREATE VIEW vw_pruebas_reactivas_mensual AS
SELECT
    c.fecha_orden_mes,
    c.anio,
    c.mes,
    p.pruebas_reactivas,
    p.pct_reactivas_consejeria,
    p.pct_reactivas_otros_programas
FROM vw_calendario_mensual c
LEFT JOIN pruebas_reactivas_cec p
    ON c.anio = p.anio;

CREATE VIEW vw_consultas_hgm_mensual AS
SELECT
    fecha_orden_mes,
    ((fecha_orden_mes - 1) / 12) AS anio,
    (((fecha_orden_mes - 1) % 12) + 1) AS mes,
    COUNT(*) AS total_consultas,
    COUNT(*) FILTER (WHERE vih_flag = 1) AS consultas_vih,
    COUNT(*) FILTER (WHERE vih_flag = 1 AND tipo_consulta ILIKE '%PRIMERA%') AS consultas_vih_primera_vez,
    COUNT(*) FILTER (WHERE vih_flag = 1 AND tipo_consulta ILIKE '%SUBSECUENTE%') AS consultas_vih_subsecuente
FROM consultas_hgm
GROUP BY fecha_orden_mes;

CREATE VIEW vw_vih_red_mensual AS
SELECT
    fecha_orden_mes,
    ((fecha_orden_mes - 1) / 12) AS anio,
    (((fecha_orden_mes - 1) % 12) + 1) AS mes,
    COUNT(*) AS muestras_total,
    AVG(cd4_a) AS cd4_promedio,
    COUNT(*) FILTER (WHERE vih_tardio_flag = 1) AS casos_cd4_bajo,
    AVG(vih_tardio_flag::double precision) AS proporcion_cd4_bajo
FROM vih_red
GROUP BY fecha_orden_mes;

CREATE VIEW vw_defunciones_mensual AS
SELECT
    fecha_orden_mes,
    ((fecha_orden_mes - 1) / 12) AS anio,
    (((fecha_orden_mes - 1) % 12) + 1) AS mes,
    COUNT(*) AS total_defunciones,
    COUNT(*) FILTER (WHERE vih_flag = 1) AS defunciones_vih
FROM defunciones
GROUP BY fecha_orden_mes;

CREATE VIEW vw_hgm_vector_cie_mensual AS
SELECT
    fecha_orden_mes,
    codigo,
    descripcion_diagnostico,
    COUNT(*) AS total_registros,
    AVG(edad) AS edad_promedio,
    MIN(edad) AS edad_minima,
    MAX(edad) AS edad_maxima,
    COUNT(*) FILTER (WHERE sexo = 1) AS total_sexo_masculino,
    COUNT(*) FILTER (WHERE sexo = 0) AS total_sexo_femenino,
    ROUND(100.0 * COUNT(*) FILTER (WHERE sexo = 1)::numeric / NULLIF(COUNT(*), 0), 2) AS pct_sexo_masculino,
    ROUND(100.0 * COUNT(*) FILTER (WHERE sexo = 0)::numeric / NULLIF(COUNT(*), 0), 2) AS pct_sexo_femenino,
    COUNT(*) FILTER (WHERE UPPER(tipo_consulta) LIKE '%PRIMERA%') AS total_primera_vez,
    COUNT(*) FILTER (WHERE UPPER(tipo_consulta) LIKE '%SUBSECUENTE%') AS total_subsecuente,
    ROUND(100.0 * COUNT(*) FILTER (WHERE UPPER(tipo_consulta) LIKE '%PRIMERA%')::numeric / NULLIF(COUNT(*), 0), 2) AS pct_primera_vez,
    ROUND(100.0 * COUNT(*) FILTER (WHERE UPPER(tipo_consulta) LIKE '%SUBSECUENTE%')::numeric / NULLIF(COUNT(*), 0), 2) AS pct_subsecuente,
    COUNT(DISTINCT especialidad) AS total_especialidades,
    MODE() WITHIN GROUP (ORDER BY especialidad) AS especialidad_principal,
    MAX(vih_flag) AS vih_flag
FROM consultas_hgm
WHERE codigo IS NOT NULL
  AND descripcion_diagnostico IS NOT NULL
GROUP BY fecha_orden_mes, codigo, descripcion_diagnostico;

CREATE VIEW vw_metricas_mensuales_integradas AS
SELECT
    c.fecha_orden_mes,
    c.anio,
    c.mes,
    COALESCE(h.total_consultas, 0) AS total_consultas,
    COALESCE(h.consultas_vih, 0) AS consultas_vih,
    CASE
        WHEN COALESCE(h.total_consultas, 0) > 0
        THEN ROUND(COALESCE(h.consultas_vih, 0)::numeric / h.total_consultas, 4)
        ELSE NULL
    END AS proporcion_consultas_vih,
    COALESCE(v.muestras_total, 0) AS muestras_total,
    v.cd4_promedio,
    COALESCE(v.casos_cd4_bajo, 0) AS casos_cd4_bajo,
    v.proporcion_cd4_bajo,
    COALESCE(d.total_defunciones, 0) AS total_defunciones,
    COALESCE(d.defunciones_vih, 0) AS defunciones_vih,
    CASE
        WHEN COALESCE(d.total_defunciones, 0) > 0
        THEN ROUND(COALESCE(d.defunciones_vih, 0)::numeric / d.total_defunciones, 4)
        ELSE NULL
    END AS proporcion_defunciones_vih,
    COALESCE(p.pruebas_reactivas, 0) AS pruebas_reactivas,
    p.pct_reactivas_consejeria,
    p.pct_reactivas_otros_programas,
    CASE
        WHEN c.fecha_orden_mes BETWEEN 24229 AND 24242 THEN 'PREPANDEMIA'
        WHEN c.fecha_orden_mes BETWEEN 24243 AND 24258 THEN 'PANDEMIA'
        WHEN c.fecha_orden_mes BETWEEN 24259 AND 24288 THEN 'POSTPANDEMIA'
        ELSE NULL
    END AS periodo
FROM vw_calendario_mensual c
LEFT JOIN vw_consultas_hgm_mensual h
    ON c.fecha_orden_mes = h.fecha_orden_mes
LEFT JOIN vw_vih_red_mensual v
    ON c.fecha_orden_mes = v.fecha_orden_mes
LEFT JOIN vw_defunciones_mensual d
    ON c.fecha_orden_mes = d.fecha_orden_mes
LEFT JOIN vw_pruebas_reactivas_mensual p
    ON c.fecha_orden_mes = p.fecha_orden_mes
ORDER BY c.fecha_orden_mes;

CREATE VIEW vw_metricas_mensuales_integradas_sexo AS
WITH sexos AS (
    SELECT *
    FROM (VALUES
        (0, 'FEMENINO_MUJER'),
        (1, 'MASCULINO_HOMBRE')
    ) AS s(sexo_codigo, sexo_etiqueta)
),
calendario AS (
    SELECT
        fecha_orden_mes,
        anio,
        mes,
        CASE
            WHEN anio < 2020 OR (anio = 2020 AND mes <= 2) THEN 'PREPANDEMIA'
            WHEN (anio = 2020 AND mes >= 3) OR (anio = 2021 AND mes <= 6) THEN 'PANDEMIA'
            ELSE 'POSTPANDEMIA'
        END AS periodo
    FROM vw_calendario_mensual
),
hgm AS (
    SELECT
        fecha_orden_mes,
        sexo AS sexo_codigo,
        COUNT(*) AS total_consultas,
        SUM(CASE WHEN vih_flag = 1 THEN 1 ELSE 0 END) AS consultas_vih,
        COUNT(*) FILTER (WHERE UPPER(tipo_consulta) LIKE '%PRIMERA%') AS consultas_primera_vez,
        COUNT(*) FILTER (WHERE UPPER(tipo_consulta) LIKE '%SUBSECUENTE%') AS consultas_subsecuente,
        AVG(edad) AS edad_promedio_consultas
    FROM consultas_hgm
    WHERE sexo IN (0, 1)
    GROUP BY fecha_orden_mes, sexo
),
vih AS (
    SELECT
        fecha_orden_mes,
        sexo AS sexo_codigo,
        COUNT(*) AS muestras_total,
        AVG(cd4_a) AS cd4_promedio,
        SUM(CASE WHEN vih_tardio_flag = 1 THEN 1 ELSE 0 END) AS casos_cd4_bajo,
        AVG(cv) AS cv_promedio,
        AVG(edad) AS edad_promedio_vih
    FROM vih_red
    WHERE sexo IN (0, 1)
    GROUP BY fecha_orden_mes, sexo
),
def AS (
    SELECT
        fecha_orden_mes,
        sexo AS sexo_codigo,
        COUNT(*) AS total_defunciones,
        SUM(CASE WHEN vih_flag = 1 THEN 1 ELSE 0 END) AS defunciones_vih,
        AVG(edad) AS edad_promedio_defunciones
    FROM defunciones
    WHERE sexo IN (0, 1)
    GROUP BY fecha_orden_mes, sexo
)
SELECT
    c.fecha_orden_mes,
    c.anio,
    c.mes,
    c.periodo,
    s.sexo_codigo,
    s.sexo_etiqueta,
    COALESCE(h.total_consultas, 0) AS total_consultas,
    COALESCE(h.consultas_vih, 0) AS consultas_vih,
    COALESCE(h.consultas_primera_vez, 0) AS consultas_primera_vez,
    COALESCE(h.consultas_subsecuente, 0) AS consultas_subsecuente,
    h.edad_promedio_consultas,
    COALESCE(v.muestras_total, 0) AS muestras_total,
    v.cd4_promedio,
    COALESCE(v.casos_cd4_bajo, 0) AS casos_cd4_bajo,
    CASE
        WHEN v.muestras_total > 0
        THEN ROUND(1.0 * v.casos_cd4_bajo::numeric / v.muestras_total, 4)
        ELSE NULL
    END AS proporcion_cd4_bajo,
    v.cv_promedio,
    v.edad_promedio_vih,
    COALESCE(d.total_defunciones, 0) AS total_defunciones,
    COALESCE(d.defunciones_vih, 0) AS defunciones_vih,
    d.edad_promedio_defunciones
FROM calendario c
CROSS JOIN sexos s
LEFT JOIN hgm h
    ON c.fecha_orden_mes = h.fecha_orden_mes
   AND s.sexo_codigo = h.sexo_codigo
LEFT JOIN vih v
    ON c.fecha_orden_mes = v.fecha_orden_mes
   AND s.sexo_codigo = v.sexo_codigo
LEFT JOIN def d
    ON c.fecha_orden_mes = d.fecha_orden_mes
   AND s.sexo_codigo = d.sexo_codigo
ORDER BY c.fecha_orden_mes, s.sexo_codigo;

CREATE VIEW vw_metricas_mensuales_integradas_grupo_edad AS
WITH grupos_edad AS (
    SELECT *
    FROM (VALUES
        (1, '00_17', 0.0, 18.0 / 130.0),
        (2, '18_24', 18.0 / 130.0, 25.0 / 130.0),
        (3, '25_34', 25.0 / 130.0, 35.0 / 130.0),
        (4, '35_44', 35.0 / 130.0, 45.0 / 130.0),
        (5, '45_54', 45.0 / 130.0, 55.0 / 130.0),
        (6, '55_64', 55.0 / 130.0, 65.0 / 130.0),
        (7, '65_MAS', 65.0 / 130.0, NULL::numeric)
    ) AS g(orden_grupo_edad, grupo_edad, limite_inferior, limite_superior)
),
calendario AS (
    SELECT
        fecha_orden_mes,
        anio,
        mes,
        CASE
            WHEN anio < 2020 OR (anio = 2020 AND mes <= 2) THEN 'PREPANDEMIA'
            WHEN (anio = 2020 AND mes >= 3) OR (anio = 2021 AND mes <= 6) THEN 'PANDEMIA'
            ELSE 'POSTPANDEMIA'
        END AS periodo
    FROM vw_calendario_mensual
),
hgm_base AS (
    SELECT
        fecha_orden_mes,
        CASE
            WHEN edad < (18.0 / 130.0) THEN '00_17'
            WHEN edad < (25.0 / 130.0) THEN '18_24'
            WHEN edad < (35.0 / 130.0) THEN '25_34'
            WHEN edad < (45.0 / 130.0) THEN '35_44'
            WHEN edad < (55.0 / 130.0) THEN '45_54'
            WHEN edad < (65.0 / 130.0) THEN '55_64'
            ELSE '65_MAS'
        END AS grupo_edad,
        COUNT(*) AS total_consultas,
        SUM(CASE WHEN vih_flag = 1 THEN 1 ELSE 0 END) AS consultas_vih,
        COUNT(*) FILTER (WHERE UPPER(tipo_consulta) LIKE '%PRIMERA%') AS consultas_primera_vez,
        COUNT(*) FILTER (WHERE UPPER(tipo_consulta) LIKE '%SUBSECUENTE%') AS consultas_subsecuente,
        AVG(edad) AS edad_promedio_consultas
    FROM consultas_hgm
    GROUP BY fecha_orden_mes, grupo_edad
),
vih_base AS (
    SELECT
        fecha_orden_mes,
        CASE
            WHEN edad < (18.0 / 130.0) THEN '00_17'
            WHEN edad < (25.0 / 130.0) THEN '18_24'
            WHEN edad < (35.0 / 130.0) THEN '25_34'
            WHEN edad < (45.0 / 130.0) THEN '35_44'
            WHEN edad < (55.0 / 130.0) THEN '45_54'
            WHEN edad < (65.0 / 130.0) THEN '55_64'
            ELSE '65_MAS'
        END AS grupo_edad,
        COUNT(*) AS muestras_total,
        AVG(cd4_a) AS cd4_promedio,
        SUM(CASE WHEN vih_tardio_flag = 1 THEN 1 ELSE 0 END) AS casos_cd4_bajo,
        AVG(cv) AS cv_promedio,
        AVG(edad) AS edad_promedio_vih
    FROM vih_red
    GROUP BY fecha_orden_mes, grupo_edad
),
def_base AS (
    SELECT
        fecha_orden_mes,
        CASE
            WHEN edad < (18.0 / 130.0) THEN '00_17'
            WHEN edad < (25.0 / 130.0) THEN '18_24'
            WHEN edad < (35.0 / 130.0) THEN '25_34'
            WHEN edad < (45.0 / 130.0) THEN '35_44'
            WHEN edad < (55.0 / 130.0) THEN '45_54'
            WHEN edad < (65.0 / 130.0) THEN '55_64'
            ELSE '65_MAS'
        END AS grupo_edad,
        COUNT(*) AS total_defunciones,
        SUM(CASE WHEN vih_flag = 1 THEN 1 ELSE 0 END) AS defunciones_vih,
        AVG(edad) AS edad_promedio_defunciones
    FROM defunciones
    GROUP BY fecha_orden_mes, grupo_edad
)
SELECT
    c.fecha_orden_mes,
    c.anio,
    c.mes,
    c.periodo,
    g.orden_grupo_edad,
    g.grupo_edad,
    COALESCE(h.total_consultas, 0) AS total_consultas,
    COALESCE(h.consultas_vih, 0) AS consultas_vih,
    COALESCE(h.consultas_primera_vez, 0) AS consultas_primera_vez,
    COALESCE(h.consultas_subsecuente, 0) AS consultas_subsecuente,
    h.edad_promedio_consultas,
    COALESCE(v.muestras_total, 0) AS muestras_total,
    v.cd4_promedio,
    COALESCE(v.casos_cd4_bajo, 0) AS casos_cd4_bajo,
    CASE
        WHEN v.muestras_total > 0
        THEN ROUND(1.0 * v.casos_cd4_bajo::numeric / v.muestras_total, 4)
        ELSE NULL
    END AS proporcion_cd4_bajo,
    v.cv_promedio,
    v.edad_promedio_vih,
    COALESCE(d.total_defunciones, 0) AS total_defunciones,
    COALESCE(d.defunciones_vih, 0) AS defunciones_vih,
    d.edad_promedio_defunciones
FROM calendario c
CROSS JOIN grupos_edad g
LEFT JOIN hgm_base h
    ON c.fecha_orden_mes = h.fecha_orden_mes
   AND g.grupo_edad = h.grupo_edad
LEFT JOIN vih_base v
    ON c.fecha_orden_mes = v.fecha_orden_mes
   AND g.grupo_edad = v.grupo_edad
LEFT JOIN def_base d
    ON c.fecha_orden_mes = d.fecha_orden_mes
   AND g.grupo_edad = d.grupo_edad
ORDER BY c.fecha_orden_mes, g.orden_grupo_edad;

