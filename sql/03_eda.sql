-- =====================================================================
-- sql/03_eda.sql
-- EDA berbasis pertanyaan bisnis, sumber: telco.features (7.043 pelanggan)
-- Dijalankan: 9 Oktober 2026
--
-- Catatan:
--   * Baseline churn = 26,5% (1.869 dari 7.043 pelanggan)
--   * Angka rupiah = hasil rescale ke ARPU Rp 46.000 (ilustratif, bukan data operator)
--   * Semua hasil adalah ASOSIASI, bukan sebab-akibat
--   * Tidak ada DECLARE (BigQuery hanya mengizinkannya di awal script);
--     parameter Q6 memakai CTE `params`
--   * Kesimpulan lengkap ada di docs/eda_findings.md
-- =====================================================================


-- =====================================================================
-- Q1a. Churn menurut kontrak: siapa paling rentan, seberapa besar kontribusinya?
-- =====================================================================
SELECT contract,
  COUNT(*)                                              AS n,
  ROUND(COUNT(*) / SUM(COUNT(*)) OVER (), 3)            AS share_cust,
  ROUND(AVG(churned), 3)                                AS churn_rate,
  ROUND(SUM(churned) / SUM(SUM(churned)) OVER (), 3)    AS share_churners
FROM `retention-simulator.telco.features`
GROUP BY 1 ORDER BY churn_rate DESC;

-- HASIL:
--   contract         n     share_cust  churn_rate  share_churners
--   Month-to-month   3875  0.550       0.427       0.886
--   One year         1473  0.209       0.113       0.089
--   Two year         1695  0.241       0.028       0.026
-- BACA: Pelanggan bulanan = 55% basis tapi 88,6% dari semua churner.


-- =====================================================================
-- Q1b. Tenure x kontrak: apakah tenure berefek sendiri di dalam tiap kontrak?
-- =====================================================================
SELECT tenure_bucket, contract,
  COUNT(*)                                              AS n,
  ROUND(AVG(churned), 3)                                AS churn_rate,
  ROUND(SUM(churned) / SUM(SUM(churned)) OVER (), 3)    AS share_churners
FROM `retention-simulator.telco.features`
GROUP BY 1, 2 ORDER BY 1, 2;

-- HASIL:
--   tenure  contract        n     churn_rate  share_churners
--   0-5     Month-to-month  1318  0.561       0.396
--   0-5     One year        32    0.125       0.002
--   0-5     Two year        21    0.000       0.000
--   12-23   Month-to-month  765   0.376       0.154
--   12-23   One year        199   0.106       0.011
--   12-23   Two year        83    0.000       0.000
--   24-47   Month-to-month  845   0.336       0.152
--   24-47   One year        510   0.098       0.027
--   24-47   Two year        269   0.019       0.003
--   48+     Month-to-month  357   0.258       0.049
--   48+     One year        662   0.131       0.047
--   48+     Two year        1284  0.033       0.023
--   6-11    Month-to-month  590   0.425       0.134
--   6-11    One year        70    0.057       0.002
--   6-11    Two year        38    0.000       0.000
-- BACA: Di dalam kontrak bulanan, churn turun seiring tenure
--   (56,1% -> 42,5% -> 37,6% -> 33,6% -> 25,8%). Pelanggan baru bulanan (0-5 bln)
--   = 39,6% dari semua churner.
-- AWAS: sel non-bulanan di tenure 0-5 dan 6-11, serta Two year 12-23, n kecil
--   (< 100). Churn 0% di sel kecil = "data tidak cukup", bukan "pasti aman".
--   Untuk pelanggan 0-5 bln, efek tenure dan efek kontrak tidak bisa dipisahkan.


-- =====================================================================
-- Q2a. Proteksi vs streaming (HANYA pelanggan berinternet; yang tanpa internet
-- otomatis 0 layanan dan akan memalsukan hubungan)
-- =====================================================================
SELECT 'protection' AS grup, n_protection AS level, COUNT(*) AS n,
       ROUND(AVG(churned), 3) AS churn_rate
FROM `retention-simulator.telco.features` WHERE has_internet = 1 GROUP BY 2
UNION ALL
SELECT 'streaming', n_streaming, COUNT(*), ROUND(AVG(churned), 3)
FROM `retention-simulator.telco.features` WHERE has_internet = 1 GROUP BY 2
ORDER BY 1, 2;

-- HASIL:
--   grup        level  n     churn_rate
--   protection  0      1267  0.567
--   protection  1      1467  0.389
--   protection  2      1372  0.238
--   protection  3      941   0.124
--   protection  4      470   0.053
--   streaming   0      2018  0.344
--   streaming   1      1559  0.314
--   streaming   2      1940  0.294
-- BACA: Proteksi: churn turun tajam (56,7% -> 5,3%, rentang 51 poin).
--   Streaming: hampir datar (34,4% -> 29,4%, rentang 5 poin).
--   Ini menjelaskan kenapa AUC n_protection (0,595) > n_addons (0,538):
--   menggabungkan streaming melemahkan sinyal.


-- =====================================================================
-- Q2b. Uji perancu: apakah efek proteksi tetap ada setelah kontrak dikendalikan?
-- =====================================================================
SELECT contract,
       IF(n_protection >= 1, 'ada proteksi', 'tanpa proteksi') AS proteksi,
       COUNT(*) AS n, ROUND(AVG(churned), 3) AS churn_rate
FROM `retention-simulator.telco.features`
WHERE has_internet = 1
GROUP BY 1, 2 ORDER BY 1, 2;

-- HASIL:
--   contract        proteksi         n     churn_rate
--   Month-to-month  ada proteksi     2148  0.397
--   Month-to-month  tanpa proteksi   1203  0.585
--   One year        ada proteksi     1052  0.137
--   One year        tanpa proteksi   57    0.228
--   Two year        ada proteksi     1050  0.040
--   Two year        tanpa proteksi   7     0.143
-- BACA: Di dalam kontrak bulanan selisihnya 18,8 poin (n besar di kedua sisi,
--   paling andal). Selisih mentah (semua kontrak) ~32 poin; setelah kontrak
--   dikendalikan ~15 poin (rata-rata tertimbang, perkiraan). Jadi sekitar separuh
--   selisih mentah adalah efek kontrak.
-- AWAS: One year tanpa proteksi n = 57; Two year tanpa proteksi n = 7 -> jangan
--   diinterpretasikan. Tenure, tagihan, dan jenis internet belum dikendalikan.


-- =====================================================================
-- Q3a. Fiber vs DSL, per kontrak (dengan rata-rata tagihan)
-- =====================================================================
SELECT internet_service, contract,
       COUNT(*) AS n, ROUND(AVG(churned), 3) AS churn_rate,
       ROUND(AVG(monthly_charge), 0) AS avg_charge
FROM `retention-simulator.telco.features`
GROUP BY 1, 2 ORDER BY 1, 2;

-- HASIL:
--   internet_service  contract        n     churn_rate  avg_charge
--   DSL               Month-to-month  1223  0.322       35671
--   DSL               One year        570   0.093       43610
--   DSL               Two year        628   0.019       50050
--   Fiber optic       Month-to-month  2128  0.546       61811
--   Fiber optic       One year        539   0.193       70163
--   Fiber optic       Two year        429   0.072       74277
--   No                Month-to-month  524   0.189       14497
--   No                One year        364   0.025       14788
--   No                Two year        638   0.008       15468
-- BACA: Fiber lebih tinggi dari DSL di SETIAP jenis kontrak, jadi bukan efek
--   kontrak. Tapi tagihan fiber ~73% lebih mahal (Rp 61,8 rb vs 35,7 rb di
--   bulanan): data ini tidak bisa memisahkan harga dari kualitas layanan.


-- =====================================================================
-- Q3b. Metode bayar x kontrak bulanan
-- =====================================================================
SELECT payment_method, is_month_to_month,
       COUNT(*) AS n, ROUND(AVG(churned), 3) AS churn_rate
FROM `retention-simulator.telco.features`
GROUP BY 1, 2 ORDER BY 1, 2;

-- HASIL:
--   payment_method              is_month_to_month  n     churn_rate
--   Bank transfer (automatic)   0                  955   0.060
--   Bank transfer (automatic)   1                  589   0.341
--   Credit card (automatic)     0                  979   0.055
--   Credit card (automatic)     1                  543   0.328
--   Electronic check            0                  515   0.150
--   Electronic check            1                  1850  0.537
--   Mailed check                0                  719   0.036
--   Mailed check                1                  893   0.316
-- BACA: Di kontrak bulanan, e-check churn 53,7% vs 31,6-34,1% metode lain.
--   Mailed check (juga manual) berperilaku seperti auto-pay -> pola ini
--   spesifik e-check, bukan "pembayaran manual" secara umum.


-- =====================================================================
-- Q3c. Uji perancu e-check x jenis internet (hanya kontrak bulanan)
-- Pertanyaan: apakah efek e-check hanya efek fiber yang menyamar?
-- =====================================================================
SELECT internet_service, is_echeck, COUNT(*) AS n, ROUND(AVG(churned), 3) AS churn_rate
FROM `retention-simulator.telco.features`
WHERE is_month_to_month = 1
GROUP BY 1, 2 ORDER BY 1, 2;

-- HASIL:
--   internet_service  is_echeck  n     churn_rate
--   DSL               0          749   0.270
--   DSL               1          474   0.405
--   Fiber optic       0          821   0.454
--   Fiber optic       1          1307  0.604
--   No                0          455   0.189
--   No                1          69    0.188
-- BACA: Perancu TIDAK terbukti. Selisih e-check bertahan ~14-15 poin di DSL
--   (+13,5) maupun fiber (+15,0). Fiber juga berdiri sendiri (~18-20 poin di atas
--   DSL pada kedua metode bayar). Sel MtM + fiber + e-check: n = 1307 (18,6%
--   basis), churn 60,4%, ~42% dari semua churner (hitungan turunan).
-- AWAS: baris "No" internet, e-check, n = 69 -> terlalu kecil. Tenure dan tagihan
--   belum dikendalikan.


-- =====================================================================
-- Q4. Di mana uangnya? Band tagihan x jumlah add-on
-- =====================================================================
SELECT
  monthly_charge_band,
  CASE WHEN n_addons = 0 THEN 'a-0 add-on'
       WHEN n_addons <= 2 THEN 'b-1 sampai 2'
       ELSE 'c-3 atau lebih' END                         AS engagement,
  COUNT(*)                                               AS n,
  ROUND(AVG(churned), 3)                                 AS churn_rate,
  ROUND(SUM(IF(churned = 1, monthly_charge, 0)) / 1e6, 2) AS rev_lost_juta_per_bulan,
  ROUND(SUM(IF(churned = 1, monthly_charge, 0))
        / SUM(SUM(IF(churned = 1, monthly_charge, 0))) OVER (), 3) AS share_rev_lost
FROM `retention-simulator.telco.features`
GROUP BY 1, 2 ORDER BY 1, 2;

-- HASIL:
--   band         engagement       n     churn_rate  rev_lost_juta  share_rev_lost
--   1-Rendah     a-0 add-on       1606  0.092       2.25           0.023
--   1-Rendah     b-1 sampai 2     237   0.325       1.89           0.019
--   1-Rendah     c-3 atau lebih   46    0.065       0.09           0.001
--   2-Menengah   a-0 add-on       613   0.533       15.16          0.153
--   2-Menengah   b-1 sampai 2     1199  0.357       21.44          0.217
--   2-Menengah   c-3 atau lebih   1067  0.103       4.93           0.050
--   3-Tinggi     b-1 sampai 2     563   0.545       19.49          0.197
--   3-Tinggi     c-3 atau lebih   1712  0.274       33.57          0.340
-- BACA: Total pendapatan bulanan hilang ~Rp 98,8 juta (ilustratif, jumlah kolom
--   rev_lost). Sel dengan churn tertinggi BUKAN sel dengan kerugian terbesar:
--   Tinggi x 3+ add-on churn 27,4% (~baseline) tapi 34,0% pendapatan hilang.
--   Empat sel terbesar (34,0 + 21,7 + 19,7 + 15,3) = ~91% pendapatan hilang.
-- AWAS: sel Rendah x 3+ add-on (n = 46) terlalu kecil. Sel Tinggi x 0 add-on
--   kosong (tidak ada pelanggan di sana), bukan error.


-- =====================================================================
-- Q5a. Baseline audit: senior citizen
-- =====================================================================
SELECT senior_citizen, COUNT(*) AS n, ROUND(AVG(churned), 3) AS churn_rate
FROM `retention-simulator.telco.features` GROUP BY 1;

-- HASIL:
--   senior_citizen  n     churn_rate
--   0               5901  0.236
--   1               1142  0.417
-- BACA: Senior churn 41,7% vs 23,6%. Model hampir pasti akan menarget senior
--   lebih banyak -> diaudit di akhir proyek (tingkat penargetan antar kelompok).


-- =====================================================================
-- Q5b. Pelanggan tenure 0
-- =====================================================================
SELECT COUNT(*) AS n_tenure0, AVG(churned) AS churn_tenure0
FROM `retention-simulator.telco.features` WHERE tenure_months = 0;

-- HASIL:
--   n_tenure0  churn_tenure0
--   11         0.0
-- KEPUTUSAN: dipertahankan (0,16% data); dicatat di Changelog assumptions.md.


-- =====================================================================
-- Q6. Jembatan ke bisnis: EV kasar per segmen
-- Memakai churn rate RATA-RATA segmen sebagai pengganti probabilitas individu
-- (nanti diganti p_churn dari model). Parameter dari docs/assumptions.md;
-- ubah di CTE `params` bila asumsi berubah.
--   EV = save_rate x margin x horizon x AVG(churned x monthly_charge) - eff_cost
--   eff_cost = biaya kontak 2.000 + take-up 0,3 x insentif 10.000 = 5.000
-- =====================================================================
WITH params AS (
  SELECT 0.25 AS save_rate, 0.40 AS margin, 12 AS horizon, 5000.0 AS eff_cost
)
SELECT
  f.tenure_bucket,
  f.contract,
  COUNT(*)                                        AS n,
  ROUND(AVG(f.churned), 3)                        AS churn_rate,
  ROUND(p.save_rate * p.margin * p.horizon * AVG(f.churned * f.monthly_charge)
        - p.eff_cost, 0)                          AS rough_ev_per_customer
FROM `retention-simulator.telco.features` AS f
CROSS JOIN params AS p
GROUP BY f.tenure_bucket, f.contract, p.save_rate, p.margin, p.horizon, p.eff_cost
ORDER BY rough_ev_per_customer DESC;

-- HASIL (save_rate 0,25):
--   tenure  contract        n     churn_rate  rough_ev_per_customer
--   0-5     Month-to-month  1318  0.561       25161
--   6-11    Month-to-month  590   0.425       22498
--   12-23   Month-to-month  765   0.376       20336
--   24-47   Month-to-month  845   0.336       19367
--   48+     Month-to-month  357   0.258       14765
--   48+     One year        662   0.131       5596
--   24-47   One year        510   0.098       1911
--   12-23   One year        199   0.106       1014
--   0-5     One year        32    0.125       721
--   48+     Two year        1284  0.033       -2427
--   6-11    One year        70    0.057       -3354
--   24-47   Two year        269   0.019       -4085
--   0-5     Two year        21    0.000       -5000
--   6-11    Two year        38    0.000       -5000
--   12-23   Two year        83    0.000       -5000
-- BACA: Semua segmen bulanan positif. One year positif tipis (rapuh terhadap
--   asumsi). Two year negatif. Nilai -5000 = churn 0 pada n kecil
--   ("data tidak cukup", bukan "pasti aman").
-- PERKIRAAN (hitungan turunan, BELUM diverifikasi dengan query): pada
--   save_rate 0,10 hanya segmen bulanan yang tetap positif; semua One year berbalik
--   negatif. Verifikasi dengan mengganti save_rate di CTE params, lalu catat
--   hasilnya di sini.
-- LIMITASI: memakai rata-rata segmen, bukan probabilitas individu.