# Model Card: Prediksi Churn Pelanggan (Retention Campaign Simulator)

> Dokumen satu halaman tentang model: untuk apa dipakai, seberapa baik, dan **kapan tidak boleh dipakai**.
> Dibuat: 12 Oktober 2026. Detail keputusan dan angka data belajar ada di `docs/model_decisions.md`.

---

## 1. Ringkasan

Model ini menghitung **peluang setiap pelanggan berhenti berlangganan (churn)**. Peluang itu dipakai di
simulator untuk menentukan siapa yang layak diberi promo retensi dengan budget tertentu.
Model ini bagian dari proyek portofolio dengan **data sampel publik**, bukan data operator nyata.

## 2. Detail model

| Item | Isi |
|---|---|
| Jenis | LightGBM (kumpulan pohon keputusan kecil), klasifikasi biner |
| Pengaturan | 300 pohon, 4 cabang per pohon, learning rate 0,03, min 40 pelanggan per daun, subsample 0,8, colsample 0,8, reg_lambda 5, seed 42 |
| Fitur | 22 fitur akun: lama berlangganan, tagihan, kontrak, metode bayar, jenis internet, layanan tambahan (proteksi, streaming), demografi dasar |
| Tidak dipakai | `gender` (keputusan etis), `charge_vs_hist` (turunan fitur lain, hasil uji fitur), ID dan band tagihan |
| Dilatih pada | 5.634 pelanggan (data belajar) |
| Perapian peluang | Tidak dipakai (hasil uji: tidak memperbaiki kejujuran peluang) |
| Pembanding | Logistic regression (C = 0,3, dengan fitur gabungan) dan tebakan rata-rata segmen |

## 3. Untuk apa model ini dipakai

- **Mengurutkan** pelanggan dari yang paling mungkin pergi, dan **memperkirakan peluangnya**, sebagai
  masukan simulasi "siapa yang layak dihubungi dengan budget X".
- Alat bantu keputusan untuk tim retensi, **dengan manusia tetap memutuskan**.

## 4. Untuk apa model ini TIDAK boleh dipakai

- **Menentukan siapa yang bisa dibujuk bertahan.** Model memprediksi *siapa yang akan pergi*, bukan *siapa
  yang akan bertahan karena promo*. Dua hal itu berbeda. Efek promo (save rate 25%) hanyalah asumsi
  dan harus divalidasi lewat A/B test.
- **Dipakai langsung di operator nyata** tanpa diuji ulang pada data operator tersebut.
- **Menilai pelanggan prabayar.** Data bergaya pascabayar; churn prabayar (berhenti top-up) didefinisikan berbeda.
- **Keputusan yang merugikan individu** (misalnya menolak layanan). Skor hanya untuk memprioritaskan penawaran.
- **Menyimpulkan sebab-akibat** dari faktor yang berpengaruh (lihat bagian 8).

## 5. Data

- Sumber: dataset sampel *Telco Customer Churn* (IBM, via Kaggle), 7.043 pelanggan, 21 kolom, churn 26,5%.
- **Snapshot** tanpa dimensi waktu: tidak ada validasi waktu (data lama vs baru).
- Nilai uang di-*rescale* ke rupiah (rata-rata tagihan = Rp 46.000, ARPU blended Telkomsel kuartal II-2026).
  Itu ilustrasi skala, bukan data operator.
- Pembagian: 80% data belajar (5 kelompok validasi silang), 20% data ujian yang dikunci dan dibuka satu kali.

## 6. Performa pada ujian akhir (1.409 pelanggan, dibuka satu kali)

Angka dalam kurung siku = rentang goyangan 95% (acak ulang pelanggan ujian 1.000 kali).

| Model | Ketepatan urutan (PR-AUC) | Daftar teratas (Lift@10%) | Kejujuran peluang (Brier, makin kecil makin baik) |
|---|---|---|---|
| Tebakan segmen | 0,527 [0,477-0,571] | 2,21 [2,00-2,61] | 0,1511 [0,1411-0,1605] |
| Logistik B | 0,682 [0,630-0,728] | 2,93 [2,61-3,27] | 0,1309 [0,1203-0,1412] |
| **LightGBM** | **0,686** [0,635-0,733] | 2,88 [2,62-3,26] | **0,1298** [0,1188-0,1400] |

Acuan: tebakan acak memberi PR-AUC ≈ 0,265, lift 1,00, brier 0,195.

- Model vs tebakan segmen: menang jelas (selisih PR-AUC +0,161, rentang 0,122-0,203).
- **LightGBM vs Logistik B: setara** (selisih +0,005, rentang -0,015 sampai +0,025, mencakup nol).
  LightGBM dipilih sebelum ujian dibuka.
- Rentang goyangan cukup lebar (±0,05) karena datanya kecil (±374 pelanggan yang pergi di data ujian).

**Menghubungi pelanggan teratas (LightGBM):**

| Hubungi teratas | Churner yang tertangkap | Jika acak |
|---|---|---|
| 10% | 28,6% | 10% |
| 20% | 51,6% | 20% |
| 30% | 69,3% | 30% |
| 50% | 88,8% | 50% |

**Kejujuran peluang:** rata-rata prediksi 25,8% vs kenyataan 26,5%. Kelompok 10% teratas: prediksi 74,0% vs
kenyataan 76,6%. Di kelompok teratas prediksi cenderung sedikit **di bawah** kenyataan (1-3 poin), jadi risiko
sedikit diremehkan, bukan dilebih-lebihkan. Selisih ini masih dalam batas kebetulan (±141 pelanggan per kelompok).

## 7. Skor yang dipakai di simulator

`data/scored.parquet` berisi peluang churn untuk semua 7.043 pelanggan, dari model yang **tidak pernah melihat
pelanggan itu** (pelanggan data belajar: dari validasi silang 5 kelompok; pelanggan data ujian: dari model
yang dilatih pada data belajar). Dengan begitu skor tidak terlalu yakin (tidak terkena efek "model menghafal").

## 8. Faktor yang paling berpengaruh pada skor (SHAP)

- **Lima faktor teratas** (rata-rata pengaruh pada skor): jenis kontrak (0,61), lama berlangganan
  (0,40), jenis internet (0,34), bayar dengan e-check (0,16), total tagihan (0,13).
- **Arah:** kontrak bulanan (+0,59 poin rata-rata), fiber (+0,36), dan lama berlangganan pendek
  menaikkan skor. Kontrak 2 tahun (-0,95), tanpa internet (-0,58), dan DSL (-0,17) menurunkan.
- **Kesesuaian dengan EDA:** sesuai untuk empat faktor teratas. Satu perbedaan: layanan streaming
  (0,12) lebih berpengaruh daripada proteksi (0,09) di dalam model, padahal di EDA streaming hampir
  tidak berhubungan dengan churn. Dugaan: model sudah mengendalikan tagihan dan jenis internet
  (belum teruji). Dicatat sebagai pengamatan tentang model, bukan temuan bisnis.
- **Fitur kembar** (kontrak, jenis internet, e-check) membagi pengaruh sehingga peringkat per fitur
  mengecilkan pengaruh gabungan informasinya.
- **Fitur hampir tak berpengaruh** (kandidat dicabut di versi berikutnya): has_partner, auto_pay,
  n_family, n_addons.

- **Cek lanjutan (pelanggan fiber dan bulanan, n = 2.128):** churn turun seiring jumlah proteksi
  (65,2% pada 0 proteksi, 30,2% pada 3 proteksi), sedangkan streaming tidak menurunkan churn
  (52,5% pada 0 streaming, 57,7% pada 2 streaming). Penurunan ringan di data keseluruhan sebagian
  adalah efek komposisi. Lama berlangganan dan tagihan belum dikendalikan, jadi ini pengamatan,
  bukan sebab-akibat.


**Cara membaca:** SHAP menunjukkan faktor mana yang mendorong skor *model* naik atau turun. Ini penjelasan
tentang **model**, bukan bukti sebab-akibat di dunia nyata. Fitur yang saling berdekatan (lama berlangganan,
total tagihan, tagihan bulanan) berbagi "jasa", jadi satu fitur tidak boleh dibaca sendirian.

## 9. Batasan dan risiko

- **Data kecil.** Selisih antar model di bawah ±0,02 PR-AUC tidak bisa dibedakan dari kebetulan.
- **Tidak ada dimensi waktu.** `tenure` dan `total_charges` pelanggan yang churn berhenti di titik kepergian,
  sedangkan pelanggan aktif terus berjalan. Performa pada pelanggan aktif nyata bisa sedikit berbeda.
- **Hanya ±20 petunjuk per pelanggan.** Hal yang sebenarnya mendorong orang berhenti (kualitas sinyal,
  tawaran pesaing, keluhan, pindah kota) tidak ada di data. Batas performa model apa pun di data ini rendah.
- **Pilihan model dibuat dari validasi silang yang sama dengan pelaporan.** Angka data belajar sedikit
  optimis; angka resmi adalah angka ujian akhir.
- **Fitur pengganti.** `gender` tidak dipakai, tetapi fitur lain bisa berkorelasi dengan atribut sensitif.
- **Konteks bisnis.** Dataset pascabayar gaya global; tidak mewakili pasar Indonesia yang didominasi prabayar.

## 10. Audit kelompok: lansia (`senior_citizen`)

Di data, pelanggan lansia churn 41,7% (n = 1.142) vs 23,6% pada non-lansia, sehingga model hampir pasti
menargetkan lebih banyak lansia. Hasil pemeriksaan pada `scored.parquet`:

- Pelanggan lansia: 1.142 orang (16,2%), churn 41,7% vs 23,6% pada non-lansia.
- **Prediksi vs kenyataan:** lansia 39,9% vs 41,7% (prediksi 1,8 poin di bawah kenyataan, dalam batas
  kebetulan, arahnya konservatif); non-lansia 23,8% vs 23,6%.
- **Di 20% skor teratas:** lansia 35,6%, non-lansia 17,0% (2,1 kali). Lansia 16,2% populasi tapi sekitar
  29% dari kelompok teratas. Sejalan dengan perbedaan risiko dasar (churn 1,8 kali lebih tinggi);
  penyebab selisih kecil antara 2,1 dan 1,8 tidak diselidiki.
- **Batas pemeriksaan:** hanya akurasi prediksi per kelompok dan tingkat keterpilihan untuk satu atribut.
  Bukan jaminan keadilan. Dampak promo terhadap kelompok ini diperiksa di Minggu 3 setelah daftar
  target terbentuk. Tidak ada perubahan model berdasarkan hasil ini.

Catatan: pemeriksaan ini dilaporkan apa adanya. Tidak ada perubahan model berdasarkan hasilnya.

## 11. Cara mereproduksi

```
python src/load_raw.py              # CSV -> BigQuery (raw)
# jalankan sql/01 sampai sql/02 di BigQuery
python src/export_features.py       # features -> data/features.parquet
python -m src.make_split            # kunci data ujian
python -m src.final_eval            # ujian akhir (SEKALI; ada segel reports/test_results.json)
python -m src.make_scored           # data/scored.parquet
python -m src.explain               # SHAP
```

## 12. Versi

| Versi | Tanggal | Perubahan |
|---|---|---|
| 1.0 | 12 Oktober 2026 | Versi awal; ujian akhir dibuka satu kali |