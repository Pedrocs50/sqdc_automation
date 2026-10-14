WITH horas_extras AS (
    SELECT
        TRUNC(fl.dat_apt, 'IW') AS semana,
        cr.sgl_cct,
        SUM(fl.vlr_tpo_apt) AS horas_extras
    FROM ckf_vop_fl_apt fl
    JOIN ckf_vop_cct cr
        ON fl.cod_estrg_cct = cr.cod_prim_cct
    JOIN ckf_vop_evnt evt
        ON fl.cod_estrg_evnt = evt.cod_prim_evnt
    WHERE evt.ind_h_extr = 1
    GROUP BY TRUNC(fl.dat_apt, 'IW'), cr.sgl_cct
),
horas_totais AS (
    SELECT
        TRUNC(fl.dat_apt, 'IW') AS semana,
        cr.sgl_cct,
        SUM(fl.vlr_tpo_apt) AS horas_totais
    FROM ckf_vop_fl_apt fl
    JOIN ckf_vop_cct cr
        ON fl.cod_estrg_cct = cr.cod_prim_cct
    JOIN ckf_vop_evnt evt
        ON fl.cod_estrg_evnt = evt.cod_prim_evnt
    WHERE evt.ind_prdt = 1
      AND fl.ind_mo_dire >= 1
    GROUP BY TRUNC(fl.dat_apt, 'IW'), cr.sgl_cct
)

SELECT
    e.semana,
    e.sgl_cct,
    e.horas_extras,
    t.horas_totais,
    ROUND(
        CASE
            WHEN t.horas_totais = 0 THEN NULL
            ELSE (e.horas_extras / t.horas_totais) * 100
        END,
        2
    ) AS perc_hora_extra
FROM horas_extras e
JOIN horas_totais t
    ON e.semana = t.semana
   AND e.sgl_cct = t.sgl_cct
ORDER BY e.semana