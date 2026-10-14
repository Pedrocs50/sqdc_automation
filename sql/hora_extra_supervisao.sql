WITH horas_extras AS (
    SELECT
        cr.sgl_cct AS cr,
        TO_CHAR(fl.dat_apt, 'IYYY') AS ano_iso,
        TO_CHAR(fl.dat_apt, 'IW') AS semana_iso,
        TRUNC(fl.dat_apt, 'IW') AS data_inicio_semana,
        TRUNC(fl.dat_apt, 'IW') + 6 AS data_fim_semana,
        SUM(fl.vlr_tpo_apt) AS horas_extras
    FROM ckf_vop_fl_apt fl
    JOIN ckf_vop_cct cr
        ON fl.cod_estrg_cct = cr.cod_prim_cct
    JOIN ckf_vop_evnt evt
        ON fl.cod_estrg_evnt = evt.cod_prim_evnt
    WHERE cr.sgl_cct IN ('S079', 'S092')
      AND evt.ind_h_extr = 1
      AND fl.dat_apt >= DATE '2026-01-01'
      AND fl.dat_apt < DATE '2027-01-01'
    GROUP BY
        cr.sgl_cct,
        TO_CHAR(fl.dat_apt, 'IYYY'),
        TO_CHAR(fl.dat_apt, 'IW'),
        TRUNC(fl.dat_apt, 'IW')
),

horas_catraca AS (
    SELECT
        cr.sgl_cct AS cr,
        TO_CHAR(fl.dat_apt, 'IYYY') AS ano_iso,
        TO_CHAR(fl.dat_apt, 'IW') AS semana_iso,
        TRUNC(fl.dat_apt, 'IW') AS data_inicio_semana,
        TRUNC(fl.dat_apt, 'IW') + 6 AS data_fim_semana,
        SUM(fl.vlr_tpo_apt) AS horas_catraca
    FROM ckf_vop_fl_apt fl
    JOIN ckf_vop_cct cr
        ON fl.cod_estrg_cct = cr.cod_prim_cct
    JOIN ckf_vop_evnt evt
        ON fl.cod_estrg_evnt = evt.cod_prim_evnt
    WHERE cr.sgl_cct IN ('S079', 'S092')
      AND evt.ind_prdt = 1
      AND fl.ind_mo_dire >= 1
      AND fl.dat_apt >= DATE '2026-01-01'
      AND fl.dat_apt < DATE '2027-01-01'
    GROUP BY
        cr.sgl_cct,
        TO_CHAR(fl.dat_apt, 'IYYY'),
        TO_CHAR(fl.dat_apt, 'IW'),
        TRUNC(fl.dat_apt, 'IW')
)

SELECT
    e.ano_iso || '_' || e.semana_iso || '_HORA_EXTRA_SUPERVISAO_' || e.cr AS title,
    TO_NUMBER(e.ano_iso) AS ano,
    TO_NUMBER(e.semana_iso) AS semanaiso,
    e.data_inicio_semana AS datainiciosemana,
    e.data_fim_semana AS datafimsemana,
    e.cr AS cr,
    ROUND(e.horas_extras, 3) AS horasextras,
    ROUND(c.horas_catraca, 3) AS horascatraca,
    ROUND(
        CASE
            WHEN c.horas_catraca = 0 THEN NULL
            ELSE (e.horas_extras / c.horas_catraca) * 100
        END,
        2
    ) AS horaextraperc,
    SYSDATE AS dataatualizacao,
    'Oracle - CKF_VOP_FL_APT / CKF_VOP_EVNT' AS fonte
FROM horas_extras e
JOIN horas_catraca c
    ON e.cr = c.cr
   AND e.ano_iso = c.ano_iso
   AND e.semana_iso = c.semana_iso
