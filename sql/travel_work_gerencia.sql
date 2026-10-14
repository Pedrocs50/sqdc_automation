-- ==========================================
-- TRAVEL WORK SEMANA ISO
-- Último valor disponível de cada semana
-- ==========================================

WITH dados_filtrados AS (
    SELECT
        dhos.DAT_ATLZ,
        dhos.NUM_HH,
        dhos.NUM_HH_SEM_ENTR
    FROM DCM.DCM_HIST_OVERVIEW_STATION dhos
    WHERE dhos.DAT_ATLZ >= DATE '2026-01-01'
      AND dhos.DAT_ATLZ <  DATE '2027-01-01'
      AND dhos.NUM_IND_STATUS_NODE_REAL = 'PASSIVO'
      AND dhos.STR_POS_KEY = 'EJET'
      AND dhos.NUM_LV = 1
      AND dhos.NUM_ORIGINALID IN (
          14139,
          14190,
          15363,
          14215,
          14162,
          14234,
          14259,
          14281
      )
),

-- Localiza a última atualização de cada dia
ultima_atualizacao_dia AS (
    SELECT
        TRUNC(DAT_ATLZ) AS dia,
        MAX(DAT_ATLZ) AS ultima_atualizacao
    FROM dados_filtrados
    GROUP BY TRUNC(DAT_ATLZ)
),

-- Soma os registros da última atualização de cada dia
total_diario AS (
    SELECT
        TRUNC(d.DAT_ATLZ) AS dia,

        SUM(NVL(d.NUM_HH, 0)) AS horas_hh,

        SUM(
            NVL(d.NUM_HH_SEM_ENTR, 0)
        ) AS horas_sem_entrave

    FROM dados_filtrados d

    INNER JOIN ultima_atualizacao_dia u
        ON d.DAT_ATLZ = u.ultima_atualizacao

    GROUP BY
        TRUNC(d.DAT_ATLZ)
),

-- Pega os valores do último dia disponível de cada semana
travel_work_semanal AS (
    SELECT
        TO_CHAR(dia, 'IYYY') AS ano_iso,

        TO_CHAR(dia, 'IW') AS semana_iso,

        TRUNC(dia, 'IW') AS data_inicio_semana,

        TRUNC(dia, 'IW') + 6 AS data_fim_semana,

        MAX(dia) AS ultimo_dia_com_dados,

        MAX(horas_hh) KEEP (
            DENSE_RANK LAST
            ORDER BY dia
        ) AS horas_ultimo_dia_semana,

        MAX(horas_sem_entrave) KEEP (
            DENSE_RANK LAST
            ORDER BY dia
        ) AS horas_sem_entrave_ultimo_dia

    FROM total_diario

    GROUP BY
        TO_CHAR(dia, 'IYYY'),
        TO_CHAR(dia, 'IW'),
        TRUNC(dia, 'IW')
)

SELECT
    t.ano_iso
        || '_'
        || t.semana_iso
        || '_TRAVEL_WORK' AS title,

    TO_NUMBER(t.ano_iso) AS ano,

    TO_NUMBER(t.semana_iso) AS semanaiso,

    t.data_inicio_semana AS datainiciosemana,

    t.data_fim_semana AS datafimsemana,

    t.ultimo_dia_com_dados AS ultimodiacomdados,

    'EJET' AS posicao,

    ROUND(
        t.horas_ultimo_dia_semana,
        3
    ) AS horasultimodiasemana,

    ROUND(
        t.horas_sem_entrave_ultimo_dia,
        3
    ) AS horassementraveultimodia,

    SYSDATE AS dataatualizacao,

    'Oracle - DCM.DCM_HIST_OVERVIEW_STATION' AS fonte

FROM travel_work_semanal t

ORDER BY
    ano,
    semanaiso;