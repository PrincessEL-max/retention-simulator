-- HASIL (dijalankan 8 Oktober 2026):
--   Query 1: n_rows = n_ids = 7043; churn_rate = 0.2654; semua cek = 0

--
-- Leakage screen, AUC tunggal (numerik, arah diabaikan):
--   tenure_months 0.740 | is_month_to_month 0.728 | is_fiber 0.673
--   is_echeck 0.661 | total_charges 0.650 | ... | charge_vs_hist 0.506
--   -> tidak ada fitur di atas ~0.85; tidak ada indikasi leakage
--   -> calon dibuang/diuji ablasi di Minggu 2: charge_vs_hist, phone_service,
--      multiple_lines; monthly_charge ~ avg_monthly_hist (redundan)
--   -> belum teruji: fitur kategorikal; arah hubungan (dijawab di EDA)


SELECT
  COUNT(*)                                          AS n_rows,
  COUNT(DISTINCT customer_id)                       AS n_ids,
  COUNTIF(churned IS NULL)                          AS null_churn,
  COUNTIF(charge_vs_hist IS NULL)                   AS null_charge_vs_hist,
  COUNTIF(avg_monthly_hist IS NULL)                 AS null_avg_hist,
  COUNTIF(n_addons NOT BETWEEN 0 AND 6)             AS bad_n_addons,
  COUNTIF(n_addons != n_protection + n_streaming)   AS n_addons_mismatch,
  COUNTIF(has_internet = 0 AND n_addons > 0)        AS addons_without_internet,
  ROUND(AVG(churned), 4)                            AS churn_rate
FROM `retention-simulator.telco.features`;

SELECT
  monthly_charge_band,
  COUNT(*)                     AS n,
  ROUND(COUNT(*) / 7043, 3)    AS share,
  ROUND(AVG(churned), 3)       AS churn_rate,
  ROUND(AVG(n_addons), 2)      AS avg_addons
FROM `retention-simulator.telco.features`
GROUP BY 1
ORDER BY 1;