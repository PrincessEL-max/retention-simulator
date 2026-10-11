# Temuan EDA: Retention Campaign Simulator

> Dibuat: <isi tanggal>. Sumber: tabel `telco.features` (7.043 pelanggan), query di `sql/03_eda.sql`.
> Semua temuan bersifat **asosiasi**, bukan sebab-akibat. Data berupa snapshot tanpa dimensi waktu.
> Angka rupiah adalah hasil rescale ke ARPU Rp 46.000 (lihat `assumptions.md`), jadi **ilustratif, bukan data operator**.

**Baseline:** 1.869 dari 7.043 pelanggan churn (**26,5%**).

Cara membaca: `n` = jumlah pelanggan di segmen. Lift = churn rate segmen dibagi 26,5%.
Sel dengan `n` kurang dari ±100 tidak dijadikan dasar kesimpulan.

---

## Temuan 1: Month-to-month memuat hampir seluruh churn

| Kontrak | n | % basis | Churn | Porsi dari seluruh churner |
|---|---|---|---|---|
| Month-to-month (MtM) | 3.875 | 55,0% | 42,7% | **88,6%** |
| One year | 1.473 | 20,9% | 11,3% | 8,9% |
| Two year | 1.695 | 24,1% | 2,8% | 2,6% |

Di dalam MtM, churn turun seiring lamanya berlangganan:

| Tenure (MtM) | n | Churn | Porsi dari seluruh churner |
|---|---|---|---|
| 0-5 bulan | 1.318 | 56,1% | 39,6% |
| 6-11 bulan | 590 | 42,5% | 13,4% |
| 12-23 bulan | 765 | 37,6% | 15,4% |
| 24-47 bulan | 845 | 33,6% | 15,2% |
| 48+ bulan | 357 | 25,8% | 4,9% |

**Temuan:** Pelanggan MtM (55% basis) menyumbang 88,6% dari seluruh churner. Pelanggan baru MtM (0-5 bulan, n = 1.318, 18,7% basis) sendirian menyumbang 39,6% churner dengan churn 56,1% (2,1× rata-rata).

**Implikasi keputusan:** Kampanye retensi difokuskan pada pelanggan MtM, terutama yang baru. Pelanggan Two year tidak layak ditarget: churn-nya 2,8% dan hampir semua biaya promo akan terbuang.

**Pembatas:** Tenure punya efek tersendiri di dalam MtM (56,1% turun ke 25,8%). Tetapi untuk pelanggan 0-5 bulan, hanya 53 pelanggan yang bukan MtM (32 One year, 21 Two year), sehingga **efek tenure dan efek kontrak tidak bisa dipisahkan** pada kelompok ini.

---

## Temuan 2: Proteksi berasosiasi dengan churn lebih rendah, streaming tidak

Analisis hanya untuk pelanggan berinternet (n = 5.517), karena pelanggan tanpa internet otomatis punya nol layanan tambahan.

| Jumlah layanan proteksi | n | Churn |
|---|---|---|
| 0 | 1.267 | 56,7% |
| 1 | 1.467 | 38,9% |
| 2 | 1.372 | 23,8% |
| 3 | 941 | 12,4% |
| 4 | 470 | 5,3% |

| Jumlah layanan streaming | n | Churn |
|---|---|---|
| 0 | 2.018 | 34,4% |
| 1 | 1.559 | 31,4% |
| 2 | 1.940 | 29,4% |

Pengujian perancu (kontrak dikendalikan):

| Kontrak | Tanpa proteksi | Ada proteksi | Selisih |
|---|---|---|---|
| Month-to-month | 58,5% (n = 1.203) | 39,7% (n = 2.148) | 18,8 poin |
| One year | 22,8% (n = 57) | 13,7% (n = 1.052) | 9,1 poin |
| Two year | 14,3% (n = 7) | 4,0% (n = 1.050) | tidak diinterpretasikan (n = 7) |

**Temuan:** Churn turun tajam seiring jumlah proteksi (56,7% ke 5,3%, rentang 51 poin), sedangkan streaming hampir datar (34,4% ke 29,4%, rentang 5 poin). Selisih mentah ada-vs-tanpa proteksi sekitar 32 poin (24,4% vs 56,7%). Setelah kontrak dikendalikan, selisih menyusut menjadi sekitar 15 poin (perkiraan, rata-rata tertimbang) dan 18,8 poin di dalam MtM saja, yang `n`-nya besar di kedua sisi dan paling andal. Sekitar separuh selisih mentah, dengan demikian, adalah efek kontrak.

**Implikasi keputusan:**
1. Untuk mengukur *engagement*, pakai jumlah proteksi, bukan total add-on. Menggabungkan streaming melemahkan sinyal (konsisten dengan AUC tunggal `n_protection` 0,595 vs `n_addons` 0,538).
2. Menawarkan proteksi (misalnya masa percobaan) ke pelanggan MtM tanpa proteksi adalah **hipotesis untuk diuji A/B**, bukan kesimpulan.

**Pembatas:** Pelanggan yang membeli proteksi mungkin memang lebih terlibat sejak awal (*self-selection*), jadi data ini tidak membuktikan bahwa memberi proteksi menurunkan churn. Tenure, tagihan, dan jenis internet belum dikendalikan. Hubungan streaming belum dikendalikan terhadap kontrak.

---

## Temuan 3: Fiber dan e-check adalah faktor risiko yang berdiri sendiri

Churn pelanggan MtM menurut jenis internet dan metode bayar:

| Internet | Bukan e-check | E-check | Selisih |
|---|---|---|---|
| DSL | 27,0% (n = 749) | 40,5% (n = 474) | +13,5 poin |
| Fiber | 45,4% (n = 821) | 60,4% (n = 1.307) | +15,0 poin |

Fiber lebih tinggi dari DSL di setiap jenis kontrak (MtM 54,6% vs 32,2%; One year 19,3% vs 9,3%; Two year 7,2% vs 1,9%). Tagihan fiber MtM rata-rata Rp 61.811 vs DSL Rp 35.671 (±73% lebih mahal). Di dalam MtM, mailed check (juga pembayaran manual) churn 31,6%, mirip auto-pay (32,8-34,1%), sehingga pola ini **spesifik e-check**, bukan pembayaran manual secara umum.

**Temuan:** E-check berasosiasi dengan churn sekitar 14-15 poin lebih tinggi di dalam pelanggan MtM, **bahkan setelah jenis internet dikendalikan**. Sekitar sepertiga selisih mentah e-check (±21 poin) adalah efek komposisi (pengguna e-check MtM lebih sering memakai fiber). Kombinasi **MtM + fiber + e-check** (n = 1.307, 18,6% basis) churn 60,4% (2,3× rata-rata) dan menyumbang ±42% dari seluruh churner.

**Implikasi keputusan:** Kombinasi ini menjadi kandidat prioritas dalam skoring dan harus dipastikan ditangkap model (fitur interaksi untuk logistic regression; LightGBM menangkapnya otomatis).

**Pembatas:** Fiber tidak terpisahkan dari harga, jadi data ini tidak bisa menjawab apakah masalahnya harga atau kualitas layanan. Mengapa e-check berasosiasi dengan churn (kurang komitmen? kurang engagement?) juga tidak bisa dijawab. Tenure dan tagihan belum dikendalikan.

---

## Temuan 4: Kerugian terbesar bukan di sel dengan churn tertinggi

Pendapatan bulanan yang hilang dari churner ±Rp 98,8 juta (ilustratif). Persilangan band tagihan × jumlah add-on:

| Band tagihan | Add-on | n | Churn | Porsi pendapatan hilang |
|---|---|---|---|---|
| Tinggi | 3 atau lebih | 1.712 | 27,4% | **34,0%** |
| Menengah | 1-2 | 1.199 | 35,7% | 21,7% |
| Tinggi | 1-2 | 563 | **54,5%** | 19,7% |
| Menengah | 0 | 613 | 53,3% | 15,3% |

Empat sel ini memuat ±91% pendapatan yang hilang. Sel Rendah × 3+ add-on (n = 46) terlalu kecil untuk diinterpretasikan. Tidak ada pelanggan di sel Tinggi × 0 add-on.

**EV kasar per segmen** (memakai churn rate segmen sebagai pengganti probabilitas individu; save rate 25%, margin 40%, horizon 12 bulan, biaya efektif Rp 5.000):

| Segmen | EV kasar per pelanggan |
|---|---|
| Semua tenure MtM | positif, Rp 14.765 sampai Rp 25.161 |
| One year | positif tipis (Rp 721 sampai Rp 5.596), kecuali 6-11 bulan (n = 70, tidak andal) |
| Two year 48+ bulan (n = 1.284) | negatif (-Rp 2.427) |
| Two year 24-47 bulan (n = 269) | negatif (-Rp 4.085) |

Sel Two year lain bernilai -Rp 5.000 karena churn 0 pada `n` kecil (21, 38, 83), yang artinya "data tidak cukup", bukan "pasti aman".

**Temuan:** Sel dengan churn tertinggi bukan sel dengan kerugian terbesar. Tinggi × 3+ add-on "hanya" churn 27,4% (hampir sama dengan baseline) tetapi menyumbang 34,0% pendapatan yang hilang karena tagihannya besar dan jumlahnya banyak. Pada asumsi awal, semua segmen MtM layak ditarget. Pada save rate 10% (batas bawah rentang uji), perkiraan saya hanya segmen MtM yang tetap positif dan seluruh One year berbalik negatif. *(Perhitungan turunan; verifikasi dengan mengubah `save_rate` di CTE `params` Q6.)*

**Implikasi keputusan:** Satu jenis promo untuk semua pelanggan tidak optimal. Pelanggan bernilai tinggi dengan risiko menengah dan pelanggan bernilai menengah dengan risiko tinggi perlu perlakuan berbeda, dasar segmentasi value-engagement di Minggu 3. Kelayakan kampanye di segmen One year rapuh terhadap asumsi save rate.

**Pembatas:** EV kasar memakai rata-rata segmen. Model di Minggu 2 menggantinya dengan probabilitas individu, sehingga bisa memisahkan pelanggan berisiko tinggi dan rendah di dalam satu segmen. Angka rupiah bergantung pada rescale ARPU blended Rp 46.000, yang mungkin mengecilkan CLV pascabayar.

---

## Pemeriksaan tambahan

| Item | Hasil | Keputusan |
|---|---|---|
| Senior citizen | Churn 41,7% (n = 1.142, 16,2% basis) vs 23,6% non-senior (n = 5.901) | Dipertahankan sebagai fitur. Model hampir pasti akan menarget senior lebih banyak, jadi diaudit di akhir proyek (perbandingan tingkat penargetan antar kelompok) |
| Tenure 0 | 11 pelanggan, churn 0 | Dipertahankan (0,16% data). Dicatat di Changelog |

## Catatan untuk Minggu 2-3

- Fitur interaksi untuk logistic regression: `is_month_to_month × is_echeck`, dan `is_month_to_month × is_fiber × is_echeck`.
- Pakai `n_protection` (bukan `n_addons`) sebagai ukuran engagement di segmentasi Minggu 3.
- Uji A/B yang layak dirancang: masa percobaan proteksi untuk MtM tanpa proteksi.
- Ablasi `charge_vs_hist` (AUC tunggal 0,506), `phone_service`, `multiple_lines`.

## Limitasi

- Data snapshot: tenure dan total_charges pelanggan churn berhenti di titik kepergian, sedangkan pelanggan aktif terus berjalan.
- Semua temuan adalah asosiasi. Pelanggan yang memilih proteksi, kontrak panjang, atau auto-pay mungkin memang berbeda sejak awal.
- Perancu yang tidak terpisahkan dari data ini: fiber vs harga, tenure vs kontrak pada pelanggan baru.
- Dataset bergaya pascabayar. Pasar Indonesia didominasi prabayar, yang definisi churn-nya berbeda.