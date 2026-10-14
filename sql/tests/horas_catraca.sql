SELECT *
FROM ckf_vop_fl_apt fl
JOIN ckf_vop_cct cr
    ON fl.cod_estrg_cct = cr.cod_prim_cct
JOIN ckf_vop_evnt evt
    ON fl.cod_estrg_evnt = evt.cod_prim_evnt
WHERE cr.sgl_cct IN ('S079', 'S092')
  AND fl.dat_apt >= DATE '2026-01-01'
  AND fl.dat_apt < DATE '2026-02-01'
ORDER BY fl.dat_apt
