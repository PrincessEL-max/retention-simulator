-- sql/01_load_and_clean.sql
DECLARE target_arpu  FLOAT64 DEFAULT 46000;   -- Rp/bulan; lihat docs/assumptions.md
DECLARE scale_factor FLOAT64;

SET scale_factor = target_arpu / (
  SELECT AVG(SAFE_CAST(MonthlyCharges AS FLOAT64))
  FROM `retention-simulator.telco.raw`
);

CREATE OR REPLACE TABLE `retention-simulator.telco.clean` AS
SELECT
  customerID                                   AS customer_id,
  gender,
  SAFE_CAST(SeniorCitizen AS INT64)            AS senior_citizen,
  CAST(Partner = 'Yes' AS INT64)               AS has_partner,
  CAST(Dependents = 'Yes' AS INT64)            AS has_dependents,
  SAFE_CAST(tenure AS INT64)                   AS tenure_months,

  CAST(PhoneService = 'Yes' AS INT64)          AS phone_service,
  CAST(MultipleLines = 'Yes' AS INT64)         AS multiple_lines,
  InternetService                              AS internet_service,   -- DSL / Fiber optic / No
  CAST(OnlineSecurity = 'Yes' AS INT64)        AS online_security,
  CAST(OnlineBackup = 'Yes' AS INT64)          AS online_backup,
  CAST(DeviceProtection = 'Yes' AS INT64)      AS device_protection,
  CAST(TechSupport = 'Yes' AS INT64)           AS tech_support,
  CAST(StreamingTV = 'Yes' AS INT64)           AS streaming_tv,
  CAST(StreamingMovies = 'Yes' AS INT64)       AS streaming_movies,

  Contract                                     AS contract,
  CAST(PaperlessBilling = 'Yes' AS INT64)      AS paperless_billing,
  PaymentMethod                                AS payment_method,

  SAFE_CAST(MonthlyCharges AS FLOAT64)         AS monthly_charge_src,
  COALESCE(SAFE_CAST(NULLIF(TRIM(TotalCharges), '') AS FLOAT64), 0) AS total_charges_src,
  SAFE_CAST(MonthlyCharges AS FLOAT64) * scale_factor               AS monthly_charge,
  COALESCE(SAFE_CAST(NULLIF(TRIM(TotalCharges), '') AS FLOAT64), 0) * scale_factor
                                                                    AS total_charges,

  CAST(Churn = 'Yes' AS INT64)                 AS churned
FROM `retention-simulator.telco.raw`;