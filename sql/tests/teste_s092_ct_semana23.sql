WITH conf AS (
    SELECT
        ord.cod_cr AS cr,
        ord.cod_ct AS ct,
        SUM(ord.qtd_h_confm) AS horas_confirmadas
    FROM ckf_spd_ordens ord
    WHERE ord.cod_cr = 'S092'
      AND TO_CHAR(
            TRUNC(ord.dat_incl_dado) -
            CASE
                WHEN ord.vlr_hor BETWEEN '00:00:00' AND '05:44:00' THEN 1
                ELSE 0
            END,
            'IYYY'
          ) = '2026'
      AND TO_CHAR(
            TRUNC(ord.dat_incl_dado) -
            CASE
                WHEN ord.vlr_hor BETWEEN '00:00:00' AND '05:44:00' THEN 1
                ELSE 0
            END,
            'IW'
          ) = '23'
    GROUP BY
        ord.cod_cr,
        ord.cod_ct
),

cat AS (
    SELECT
        cr.sgl_cct AS cr,
        fl.cod_estrg_cct,
        SUM(fl.vlr_tpo_apt) AS horas_catraca
    FROM ckf_vop_fl_apt fl
    JOIN ckf_vop_cct cr
        ON fl.cod_estrg_cct = cr.cod_prim_cct
    JOIN ckf_vop_evnt evt
        ON fl.cod_estrg_evnt = evt.cod_prim_evnt
    WHERE cr.sgl_cct = 'S092'
      AND evt.ind_prdt = 1
      AND fl.ind_mo_dire >= 1
      AND TO_CHAR(fl.dat_apt, 'IYYY') = '2026'
      AND TO_CHAR(fl.dat_apt, 'IW') = '23'
    GROUP BY
        cr.sgl_cct,
        fl.cod_estrg_cct
)

SELECT
    c.cr,
    c.ct,
    ROUND(c.horas_confirmadas, 3) AS horas_confirmadas,
    ROUND(NVL(t.horas_catraca, 0), 3) AS horas_catraca,
    ROUND(
        CASE
            WHEN NVL(t.horas_catraca, 0) = 0 THEN NULL
            ELSE (c.horas_confirmadas / t.horas_catraca) * 100
        END,
        2
    ) AS iuh
FROM conf c
LEFT JOIN cat t
    ON c.cr = t.cr
ORDER BY iuh DESC NULLS LAST, c.ct
