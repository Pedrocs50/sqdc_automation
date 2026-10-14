SELECT
    CASE
        WHEN ord.cod_cr = 'S079' THEN 'Junção'
        WHEN ord.cod_cr = 'S092' THEN 'Pintura'
        ELSE 'Outros'
    END AS cr,
    TO_NUMBER(TO_CHAR(TRUNC(ord.dat_incl_dado), 'IYYY')) AS ano,
    TO_NUMBER(TO_CHAR(TRUNC(ord.dat_incl_dado), 'IW')) AS semanaiso,
    ROUND(SUM(ord.qtd_h_confm), 3) AS horasconfirmadas
FROM ckf_spd_ordens ord
WHERE ord.cod_cr IN ('S079', 'S092')
  AND ord.dat_incl_dado >= DATE '2026-01-01'
  AND ord.dat_incl_dado < DATE '2027-01-01'
GROUP BY
    CASE
        WHEN ord.cod_cr = 'S079' THEN 'Junção'
        WHEN ord.cod_cr = 'S092' THEN 'Pintura'
        ELSE 'Outros'
    END,
    TO_CHAR(TRUNC(ord.dat_incl_dado), 'IYYY'),
    TO_CHAR(TRUNC(ord.dat_incl_dado), 'IW')
ORDER BY ano, semanaiso, cr