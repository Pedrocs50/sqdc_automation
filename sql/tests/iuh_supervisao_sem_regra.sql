WITH conf AS (
    SELECT
        ord.cod_cr AS cr,

        TO_CHAR(TRUNC(ord.dat_incl_dado), 'IYYY') AS ano_iso,
        TO_CHAR(TRUNC(ord.dat_incl_dado), 'IW') AS semana_iso,

        TRUNC(TRUNC(ord.dat_incl_dado), 'IW') AS data_inicio_semana,
        TRUNC(TRUNC(ord.dat_incl_dado), 'IW') + 6 AS data_fim_semana,

        SUM(ord.qtd_h_confm) AS horas_confirmadas
    FROM ckf_spd_ordens ord
    WHERE ord.cod_cr IN ('S079', 'S092')
      AND TO_CHAR(ord.dat_incl_dado, 'YYYY') = '2026'
    GROUP BY
        ord.cod_cr,
        TO_CHAR(TRUNC(ord.dat_incl_dado), 'IYYY'),
        TO_CHAR(TRUNC(ord.dat_incl_dado), 'IW'),
        TRUNC(TRUNC(ord.dat_incl_dado), 'IW')
),

cat AS (
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
      AND TO_CHAR(fl.dat_apt, 'YYYY') = '2026'
    GROUP BY
        cr.sgl_cct,
        TO_CHAR(fl.dat_apt, 'IYYY'),
        TO_CHAR(fl.dat_apt, 'IW'),
        TRUNC(fl.dat_apt, 'IW')
)

SELECT
    c.ano_iso || '_' || c.semana_iso || '_IUH_SUPERVISAO_' || c.cr AS title,
    TO_NUMBER(c.ano_iso) AS ano,
    TO_NUMBER(c.semana_iso) AS semanaiso,
    c.data_inicio_semana AS datainiciosemana,
    c.data_fim_semana AS datafimsemana,
    c.cr,
    ROUND(c.horas_confirmadas, 3) AS horasconfirmadas,
    ROUND(t.horas_catraca, 3) AS horascatraca,
    ROUND(
        (c.horas_confirmadas / t.horas_catraca) * 100,
        2
    ) AS iuh
FROM conf c
JOIN cat t
    ON c.cr = t.cr
   AND c.ano_iso = t.ano_iso
   AND c.semana_iso = t.semana_iso
ORDER BY ano, semanaiso, cr