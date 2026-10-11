-- sql/02_features.sql
-- Sumber: telco.clean. Satu baris per pelanggan.
-- Sengaja TIDAK dimasukkan: gender (keputusan etis), *_src (duplikat versi rupiah)

CREATE OR REPLACE TABLE `retention-simulator.telco.features` AS
WITH base AS (
  SELECT
    *,
    SAFE_DIVIDE(total_charges, NULLIF(tenure_months, 0)) AS avg_hist_raw
  FROM `retention-simulator.telco.clean`
)
SELECT
  customer_id,
  churned,                                   -- target

  -- Numerik dasar
  tenure_months,
  monthly_charge,
  total_charges,

  -- Band tagihan (rupiah, batas tetap; hanya untuk EDA/segmentasi)
  CASE
    WHEN monthly_charge < 30000 THEN '1-Rendah'
    WHEN monthly_charge < 60000 THEN '2-Menengah'
    ELSE '3-Tinggi'
  END AS monthly_charge_band,

  -- Segmentasi tenure
  CASE
    WHEN tenure_months < 6  THEN '0-5'
    WHEN tenure_months < 12 THEN '6-11'
    WHEN tenure_months < 24 THEN '12-23'
    WHEN tenure_months < 48 THEN '24-47'
    ELSE '48+'
  END AS tenure_bucket,

  -- Riwayat harga (tenure 0 -> pakai tagihan sekarang, jadi selisih = 0)
  COALESCE(avg_hist_raw, monthly_charge)                              AS avg_monthly_hist,
  SAFE_DIVIDE(monthly_charge, COALESCE(avg_hist_raw, monthly_charge)) - 1
                                                                      AS charge_vs_hist,

  -- Engagement layanan
  online_security + online_backup + device_protection + tech_support  AS n_protection,
  streaming_tv + streaming_movies                                     AS n_streaming,
  online_security + online_backup + device_protection + tech_support
    + streaming_tv + streaming_movies                                 AS n_addons,

  -- Struktur akun
  contract,
  CAST(contract = 'Month-to-month' AS INT64)                          AS is_month_to_month,
  payment_method,
  CAST(payment_method IN ('Bank transfer (automatic)', 'Credit card (automatic)') AS INT64)
                                                                      AS auto_pay,
  CAST(payment_method = 'Electronic check' AS INT64)                  AS is_echeck,
  paperless_billing,

  -- Layanan inti
  internet_service,
  CAST(internet_service != 'No' AS INT64)                             AS has_internet,
  CAST(internet_service = 'Fiber optic' AS INT64)                     AS is_fiber,
  phone_service,
  multiple_lines,

  -- Demografi
  senior_citizen,
  has_partner,
  has_dependents,
  has_partner + has_dependents                                        AS n_family
FROM base;