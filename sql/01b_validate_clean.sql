-- sql/01b_validate_clean.sql
-- Validasi tabel telco.clean setelah 01_load_and_clean.sql
--
-- HASIL (dijalankan 8 Oktober 2026):
--   n_rows = n_ids = 7043       -> tidak ada baris hilang atau duplikat vs raw
--   null_monthly/tenure/churn = 0
--   avg_monthly_idr = 46000     -> rescale berhasil, sama dengan target ARPU
--   churn_rate = 0.2654         -> baseline PR-AUC model acak ≈ 0.27
--   n_tenure0 = 11, n_tenure0_churn = 0
--       -> 11 pelanggan baru, tidak ada yang churn; dipertahankan,
--          dicek ulang di EDA
--   scale_factor = 710.296446128027

SELECT
  COUNT(*)                                         AS n_rows,
  COUNT(DISTINCT customer_id)                      AS n_ids,
  COUNTIF(monthly_charge IS NULL)                  AS null_monthly,
  COUNTIF(tenure_months IS NULL)                   AS null_tenure,
  COUNTIF(churned IS NULL)                         AS null_churn,
  ROUND(AVG(monthly_charge), 0)                    AS avg_monthly_idr,
  ROUND(AVG(churned), 4)                           AS churn_rate,
  COUNTIF(tenure_months = 0)                       AS n_tenure0,
  COUNTIF(tenure_months = 0 AND churned = 1)       AS n_tenure0_churn
FROM `retention-simulator.telco.clean`;

SELECT 46000 / AVG(SAFE_CAST(MonthlyCharges AS FLOAT64)) AS scale_factor
FROM `retention-simulator.telco.raw`;