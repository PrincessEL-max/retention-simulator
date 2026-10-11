## Cara menjalankan
1. Unduh dataset Telco Customer Churn dari Kaggle, simpan di `data/raw/`
2. Buat project BigQuery (sandbox) dan dataset `telco`
3. `gcloud auth application-default login`
4. `export GCP_PROJECT_ID=<project-id>`
5. `python src/load_raw.py`

Catatan: tabel di BigQuery sandbox kedaluwarsa setelah 60 hari;
jalankan ulang langkah 5 dan skrip SQL di folder `sql/` untuk membangun ulang.