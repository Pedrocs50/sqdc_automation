SELECT *
FROM ckf_spd_ordens ord
WHERE ord.cod_cr IN ('S079', 'S092')
  AND ord.dat_incl_dado >= DATE '2026-01-01'
  AND ord.dat_incl_dado < DATE '2026-02-01'
ORDER BY ord.dat_incl_dado