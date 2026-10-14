WITH cat AS (
    SELECT
        cr.sgl_cct AS cr,
        TO_CHAR(fl.dat_apt, 'IYYY') AS ano_iso,
        TO_CHAR(fl.dat_apt, 'IW') AS semana_iso,
        SUM(fl.vlr_tpo_apt) AS horas_catraca
    FROM ckf_vop_fl_apt fl
    JOIN ckf_vop_cct cr
        ON fl.cod_estrg_cct = cr.cod_prim_cct
    JOIN ckf_vop_evnt evt
        ON fl.cod_estrg_evnt = evt.cod_prim_evnt
    WHERE cr.sgl_cct = 'S092'
      AND evt.ind_prdt = 1
      AND fl.ind_mo_dire >= 1
      AND TO_CHAR(fl.dat_apt, 'YYYY') = '2026'
      AND TO_CHAR(fl.dat_apt, 'IW') IN ('22', '23')
    GROUP BY
        cr.sgl_cct,
        TO_CHAR(fl.dat_apt, 'IYYY'),
        TO_CHAR(fl.dat_apt, 'IW')
),

conf_com_regra AS (
    SELECT
        ord.cod_cr AS cr,
        TO_CHAR(
            TRUNC(ord.dat_incl_dado) -
            CASE
                WHEN ord.vlr_hor BETWEEN '00:00:00' AND '05:44:00' THEN 1
                ELSE 0
            END,
            'IYYY'
        ) AS ano_iso,
        TO_CHAR(
            TRUNC(ord.dat_incl_dado) -
            CASE
                WHEN ord.vlr_hor BETWEEN '00:00:00' AND '05:44:00' THEN 1
                ELSE 0
            END,
            'IW'
        ) AS semana_iso,
        SUM(ord.qtd_h_confm) AS horas_confirmadas
    FROM ckf_spd_ordens ord
    WHERE ord.cod_cr = 'S092'
      AND TO_CHAR(ord.dat_incl_dado, 'YYYY') = '2026'
    GROUP BY
        ord.cod_cr,
        TO_CHAR(
            TRUNC(ord.dat_incl_dado) -
            CASE
                WHEN ord.vlr_hor BETWEEN '00:00:00' AND '05:44:00' THEN 1
                ELSE 0
            END,
            'IYYY'
        ),
        TO_CHAR(
            TRUNC(ord.dat_incl_dado) -
            CASE
                WHEN ord.vlr_hor BETWEEN '00:00:00' AND '05:44:00' THEN 1
                ELSE 0
            END,
            'IW'
        )
),

conf_sem_regra AS (
    SELECT
        ord.cod_cr AS cr,
        TO_CHAR(TRUNC(ord.dat_incl_dado), 'IYYY') AS ano_iso,
        TO_CHAR(TRUNC(ord.dat_incl_dado), 'IW') AS semana_iso,
        SUM(ord.qtd_h_confm) AS horas_confirmadas
    FROM ckf_spd_ordens ord
    WHERE ord.cod_cr = 'S092'
      AND TO_CHAR(ord.dat_incl_dado, 'YYYY') = '2026'
    GROUP BY
        ord.cod_cr,
        TO_CHAR(TRUNC(ord.dat_incl_dado), 'IYYY'),
        TO_CHAR(TRUNC(ord.dat_incl_dado), 'IW')
)

SELECT
    'COM_REGRA_HORARIO' AS metodo,
    c.ano_iso,
    c.semana_iso,
    c.cr,
    ROUND(c.horas_confirmadas, 3) AS horas_confirmadas,
    ROUND(t.horas_catraca, 3) AS horas_catraca,
    ROUND(
        CASE
            WHEN t.horas_catraca = 0 THEN NULL
            ELSE (c.horas_confirmadas / t.horas_catraca) * 100
        END,
        2
    ) AS iuh
FROM conf_com_regra c
JOIN cat t
    ON c.cr = t.cr
   AND c.ano_iso = t.ano_iso
   AND c.semana_iso = t.semana_iso
WHERE c.semana_iso IN ('22', '23')

UNION ALL

SELECT
    'SEM_REGRA_HORARIO' AS metodo,
    c.ano_iso,
    c.semana_iso,
    c.cr,
    ROUND(c.horas_confirmadas, 3) AS horas_confirmadas,
    ROUND(t.horas_catraca, 3) AS horas_catraca,
    ROUND(
        CASE
            WHEN t.horas_catraca = 0 THEN NULL
            ELSE (c.horas_confirmadas / t.horas_catraca) * 100
        END,
        2
    ) AS iuh
FROM conf_sem_regra c
JOIN cat t
    ON c.cr = t.cr
   AND c.ano_iso = t.ano_iso
   AND c.semana_iso = t.semana_iso
WHERE c.semana_iso IN ('22', '23')

ORDER BY semana_iso, metodo