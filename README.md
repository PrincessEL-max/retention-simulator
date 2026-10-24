# Retention Campaign Simulator

> Pelanggan mana yang layak diberi promo retensi supaya untung bersih paling besar, dengan budget terbatas?

![Demo simulator](docs/demo.gif)

**Aplikasi:** https://retention-simulator-tafa.streamlit.app/ · **Model card:** [docs/model_card.md](docs/model_card.md) · **Temuan bisnis:** [docs/business_findings.md](docs/business_findings.md)

---

## 1. Masalah bisnis

Promo retensi itu mahal. Menghubungi semua pelanggan membuang budget pada orang yang tidak akan pergi atau
nilainya kecil, sedangkan menghubungi orang yang salah tidak menyelamatkan siapa pun. Proyek ini menjawab tiga
pertanyaan: **siapa yang dihubungi, berapa budget yang masuk akal, dan seberapa yakin kita bahwa hitungannya benar.**

## 2. Ringkasan hasil

Semua angka rupiah di bawah adalah **perkiraan di bawah asumsi**: margin 40%, horizon 12 bulan, **save rate 25%**,
biaya efektif Rp 5.000 per orang yang dihubungi. Save rate (peluang promo menahan calon churner) adalah asumsi
yang belum dibuktikan; rancangan A/B test untuk mengukurnya ada di bagian 6.

- **Hanya 59,6% pelanggan (4.195 dari 7.043) layak dihubungi.** Menghubungi mereka: biaya Rp 21,0 juta, untung bersih
  Rp 92,7 juta. Menghubungi semua: biaya Rp 35,2 juta, untung Rp 83,4 juta. Selisih Rp 9,3 juta (rentang 95%: 8,4 sampai 10,1).
- **Pada budget Rp 10 juta**, memilih pelanggan berdasarkan untung bersih menghasilkan Rp 74,7 juta, sekitar 3,2 kali
  memilih acak (Rp 23,7 juta).
- **Berhenti di waktu yang tepat adalah penghematan terbesar.** "Urut untung" hanya sedikit lebih baik dari "urut risiko"
  (+Rp 2,4 juta; rentang 95%: 0,95 sampai 3,86).
- **Yang kokoh:** keputusan "pilih pelanggan, jangan hubungi semua" bertahan pada save rate 5% sampai 40%.
  **Yang rapuh:** besar untungnya (Rp 26 juta pada save rate 10% sampai Rp 162 juta pada 40%).
- **Titik impas:** kampanye rugi jika save rate di bawah **4,6%**.
- **Model churn** (LightGBM) pada ujian akhir yang dikunci (1.409 pelanggan): PR-AUC 0,686 [0,635 sampai 0,733],
  lift@10% 2,88. Menghubungi 20% pelanggan teratas menangkap 51,6% dari yang akan pergi. Setara dengan logistic
  regression (selisih +0,005, rentang -0,015 sampai +0,025).

## 3. Data dan lisensi

- **Sumber:** *Telco Customer Churn* dari IBM Sample Data Sets: perusahaan telekomunikasi **fiktif**, 7.043 pelanggan,
  21 kolom, churn 26,5%. Repo IBM: <https://github.com/IBM/telco-customer-churn-on-icp4d> (Apache License 2.0).
- **Yang dipublikasikan di repo ini:** hanya file turunan minimal `app/app_data.parquet` (11 kolom + penjelasan
  model). **CSV mentah tidak disertakan.** Perubahan yang dilakukan dijelaskan di [NOTICE](NOTICE): nilai uang
  diskalakan ke rupiah (rata-rata tagihan Rp 46.000, mengikuti ARPU blended Telkomsel kuartal II-2026), ID
  diganti dan urutan diacak, `gender` tidak dipakai.
- Rupiah hanya **ilustrasi skala**, bukan data operator.

## 4. Pendekatan

| Langkah | Isi | Berkas |
|---|---|---|
| Data | Muat ke BigQuery sebagai teks mentah, bersihkan dengan SQL, bangun fitur, cek kebocoran per fitur | `sql/`, `src/load_raw.py` |
| EDA | Enam pertanyaan bisnis, kontrol perancu, temuan dalam kalimat bisnis | `sql/03_eda.sql`, `docs/eda_findings.md` |
| Model | Data ujian 20% dikunci; pembanding tebakan segmen, logistic regression, LightGBM; uji kalibrasi dan fitur; ujian akhir **satu kali** dengan segel | `src/`, `docs/model_decisions.md` |
| Skor | Peluang churn dari model yang tidak pernah melihat pelanggan itu; penjelasan SHAP | `src/make_scored.py`, `src/explain.py` |
| Nilai bisnis | Untung bersih = peluang pergi × save rate × nilai pelanggan − biaya | `src/value.py` |
| Keputusan | Bandingkan acak, urut risiko, urut untung pada budget yang sama; uji kepekaan; segmen | `src/strategies.py`, `src/sensitivity.py`, `src/segments.py` |
| Validasi | Rancangan A/B test dan simulasi aturan keputusan | `src/experiment.py`, `docs/experiment_design.md` |
| Aplikasi | Simulator interaktif (Streamlit) | `app/streamlit_app.py` |

## 5. Temuan dan rekomendasi

1. **Kontrak bulanan memuat hampir seluruh churn.** 55% pelanggan, 88,6% dari yang pergi; pelanggan baru bulanan
   (0 sampai 5 bulan) sendirian 39,6%. Kontrak 2 tahun tidak layak ditarget.
2. **Proteksi berasosiasi dengan churn lebih rendah**, sebagian karena kontrak (selisih mentah ±32 poin, ±15 poin
   setelah kontrak dikendalikan). Streaming tidak. Ini hipotesis untuk A/B test, bukan sebab-akibat.
3. **Fiber dan e-check adalah faktor risiko yang berdiri sendiri** (bulanan + fiber + e-check: churn 60,4%,
   ±42% dari seluruh churner), tetapi penyebabnya (harga atau kualitas) tidak terpisahkan dari data ini.
4. **Kerugian terbesar bukan di sel dengan churn tertinggi.** Segmen tagihan tinggi dengan proteksi 1-2 menyumbang
   37% untung bersih; empat segmen teratas = 91% untung dari 54% pelanggan.

**Rekomendasi:** fokus pada pelanggan bulanan bernilai menengah dan tinggi; jangan hubungi pelanggan di luar daftar
layak; uji dulu dengan kelompok kontrol sebelum menaikkan budget.

## 6. Rencana validasi (A/B test)

Model memprediksi **siapa yang akan pergi**, bukan **siapa yang bisa ditahan**. Save rate hanya bisa diukur dengan
kelompok kontrol. Rancangan: kontrol (tidak dihubungi) vs promo standar pada pelanggan layak, diacak per segmen, churn 90
hari; lanjutkan jika batas bawah rentang 95% save rate di atas 4,6%. Pada data sebesar ini (4.195 pelanggan), uji
hanya memberi jawaban jelas jika save rate sebenarnya ≥ 15%. Itu batas dataset, bukan batas rancangan.
Detail: [docs/experiment_design.md](docs/experiment_design.md).

## 7. Batas yang perlu diketahui

- **Save rate adalah asumsi.** Semua angka rupiah bergantung padanya.
- Data **snapshot** tanpa dimensi waktu; `tenure` dan `total_charges` pelanggan yang pergi berhenti di titik kepergian.
- Dataset bergaya pascabayar; pasar Indonesia didominasi prabayar.
- Hanya ±20 petunjuk per pelanggan; kualitas sinyal, tawaran pesaing, dan keluhan tidak ada di data.
- Semua temuan adalah **asosiasi**. Fitur yang mirip saling berbagi pengaruh pada penjelasan model.
- Pemeriksaan kelompok lansia hanya mencakup akurasi prediksi dan tingkat keterpilihan, bukan jaminan keadilan.

## 8. Struktur repo

```
├── app/              aplikasi Streamlit dan data turunan minimal
├── docs/             asumsi, temuan, keputusan model, model card, rancangan A/B test
├── notebooks/        EDA, modeling, nilai, strategi, kepekaan, segmen, eksperimen
├── reports/          grafik dan tabel hasil, segel ujian akhir
├── sql/              profiling, pembersihan, fitur, EDA, validasi
├── src/              kode (data, model, nilai, strategi, kepekaan, eksperimen)
├── LICENSE           Apache 2.0
├── NOTICE            atribusi data dan pernyataan perubahan
├── requirements.txt  untuk menjalankan aplikasi
└── requirements-dev.txt  untuk mereproduksi seluruh analisis
```

## 9. Cara menjalankan

**Hanya aplikasi** (tanpa BigQuery, memakai `app/app_data.parquet`):

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows; Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app/streamlit_app.py
```

**Reproduksi seluruh analisis** (butuh akun Google Cloud, sandbox BigQuery gratis):

1. Unduh data dari repo IBM di atas, simpan sebagai `data/raw/WA_Fn-UseC_-Telco-Customer-Churn.csv`.
2. `pip install -r requirements-dev.txt`, lalu `gcloud auth application-default login` dan set `GCP_PROJECT_ID`.
3. `python src/load_raw.py`, lalu jalankan `sql/01_load_and_clean.sql` dan `sql/02_features.sql` di BigQuery.
4. `python src/export_features.py`, `python -m src.make_split`.
5. `python -m src.final_eval` (ujian akhir; di salinan Anda sendiri hapus `reports/test_results.json` lebih dulu,
   karena itu segel yang menandai ujian sudah dijalankan satu kali di proyek asli).
6. `python -m src.make_scored`, `python -m src.explain`, `python -m src.make_app_data`.

Tabel BigQuery sandbox kedaluwarsa setelah 60 hari; jalankan ulang langkah 3 untuk membangunnya kembali.

## 10. Atribusi dan lisensi

Kode dan data turunan dilisensikan di bawah Apache License 2.0 ([LICENSE](LICENSE)). Data berasal dari IBM Sample Data Sets
(Telco Customer Churn), hak cipta IBM, Apache License 2.0; perubahan dijelaskan di [NOTICE](NOTICE).
Proyek ini bukan produk IBM dan tidak didukung atau disahkan oleh IBM.
Jika pemegang hak cipta keberatan, file data turunan ini akan segera dihapus.