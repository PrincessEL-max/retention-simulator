# Keputusan Model: Retention Campaign Simulator

> Status: **ujian akhir (test set) BELUM dibuka.** Semua angka di bawah berasal dari data belajar (dev)
> dengan validasi silang 5 kelompok, kecuali disebut lain. Pilihan model, pengaturan, dan fitur dibuat
> dari data belajar saja.
> Dibuat: 11 Oktober 2026

---

## 1. Pembagian data

| Bagian | Jumlah | Churn | Fungsi |
|---|---|---|---|
| Data belajar (dev) | 5.634 | 26,5% | Memilih model, pengaturan, dan fitur. Dibagi 5 kelompok (±1.127 pelanggan per kelompok) |
| Data ujian (test) | 1.409 | 26,5% | **Dikunci.** Dibuka satu kali di Step 11 |

Pembagian: acak dengan proporsi churn dijaga sama (*stratified*), `random_state = 42`. ID pelanggan tidak
tumpang tindih antara dev dan test (diperiksa otomatis di `src/final_eval.py`).

## 2. Ukuran yang dipakai

| Ukuran | Arti sederhana | Lebih baik kalau | Acak |
|---|---|---|---|
| PR-AUC (ketepatan urutan) | Seberapa rapi pelanggan berisiko naik ke atas daftar | Lebih besar | ≈ 0,265 |
| Lift@10% (daftar teratas) | 10% teratas berisi churner berapa kali lebih banyak dari acak | Lebih besar | 1,00 |
| Brier (kejujuran peluang) | Seberapa dekat angka peluang dengan kenyataan | Lebih kecil | 0,195 |

Akurasi tidak dilaporkan karena menyesatkan pada data tidak seimbang (±26,5% churn).
Rentang antar-kelompok pada hasil di bawah = nilai terendah dan tertinggi dari 5 kelompok.
Datanya kecil, jadi skor antar-kelompok naik-turun sekitar ±0,06; selisih antar model yang jauh lebih kecil
dari itu tidak dianggap pasti.

## 3. Pembanding: tebakan segmen

Setiap pelanggan diberi skor = rata-rata churn di segmen (lama berlangganan × jenis kontrak) miliknya.
Ini cara yang sama dengan perhitungan EV kasar di EDA.

| PR-AUC | Rentang antar-kelompok | Lift@10% | Brier |
|---|---|---|---|
| 0,481 | 0,456 - 0,539 | 1,95 | 0,1580 |

Keterbatasannya: semua pelanggan dalam satu segmen mendapat angka yang sama, jadi tidak bisa membedakan
pelanggan berisiko tinggi dan rendah di dalam satu segmen. Itu yang diisi model.

## 4. Logistic regression (model sederhana)

| Versi | PR-AUC | Rentang | Lift@10% | Brier |
|---|---|---|---|---|
| A (dasar) | 0,642 | 0,623 - 0,676 | 2,76 | 0,1372 |
| **B (+ fitur gabungan)** | **0,645** | 0,624 - 0,681 | **2,80** | **0,1365** |

- Keduanya menang di 5 dari 5 kelompok atas tebakan segmen.
- B vs A: menang 5 dari 5 kelompok, tetapi selisih hanya +0,003. Praktis seri. B dipakai sebagai pembanding.
- Fitur gabungan dari temuan EDA: bulanan × e-check, bulanan × fiber, bulanan × fiber × e-check,
  bulanan × lama berlangganan. Hanya "bulanan × lama berlangganan" berbobot jelas (-0,41); tiga lainnya
  mendekati nol (sejalan dengan temuan EDA bahwa fiber dan e-check kira-kira saling menambah).
- Pilihan `C` (seberapa hati-hati model), semua dari data belajar:

| C | PR-AUC | Lift@10% | Brier |
|---|---|---|---|
| 0,03 | 0,641 | 2,77 | 0,1372 |
| 0,1 | 0,644 | 2,78 | 0,1366 |
| **0,3** | 0,645 | 2,80 | 0,1365 |
| 1 | 0,645 | 2,80 | 0,1365 |
| 3 | 0,645 | 2,78 | 0,1366 |

Aturan: brier terkecil; kalau seri, pilih `C` lebih kecil. Terpilih **C = 0,3**.

Bobot terbesar (model B, saat `charge_vs_hist` masih ada): menaikkan risiko: kontrak bulanan (+1,33),
fiber (+0,64), e-check (+0,33). Menurunkan risiko: kontrak 2 tahun (-1,12), punya telepon (-0,68),
tanpa internet (-0,60). Arahnya sesuai temuan EDA, kecuali `phone_service` (lihat bagian 8).
Bobot menunjukkan hubungan, bukan sebab-akibat.

## 5. LightGBM (model utama)

Pengaturan awal dan lima pengaturan yang dicoba (hanya lima, agar tidak mencari-cari sampai ketemu yang bagus):

| Pengaturan | PR-AUC | Lift@10% | Brier |
|---|---|---|---|
| 300 pohon, 8 cabang (awal) | 0,654 | 2,82 | 0,1351 |
| 150 pohon, 4 cabang | 0,651 | 2,78 | 0,1363 |
| **300 pohon, 4 cabang** | **0,656** | 2,82 | **0,1348** |
| 300 pohon, 8 cabang | 0,654 | 2,82 | 0,1351 |
| 500 pohon, 8 cabang, learning rate 0,02 | 0,653 | 2,79 | 0,1353 |
| 300 pohon, 16 cabang | 0,647 | 2,82 | 0,1368 |

Terpilih: **300 pohon, 4 cabang**, `learning_rate = 0,03`, `min_child_samples = 40`, `subsample = 0,8`,
`colsample_bytree = 0,8`, `reg_lambda = 5`, `random_state = 42`.
Pohon yang lebih besar (16 cabang) justru lebih buruk: tanda mulai menghafal data belajar.

**LightGBM vs Logistik B:** menang di 5 dari 5 kelompok dengan selisih konsisten ±0,010 sampai 0,015 per
kelompok. Selisih rata-rata PR-AUC **+0,011** (zona abu-abu), jauh di bawah naik-turun antar-kelompok (±0,06).
Keputusan: LightGBM jadi model utama karena sedikit lebih baik di ketiga ukuran, termasuk kejujuran peluang.
Logistik B jadi pembanding dan alat penjelas.

**Dicoba tapi tidak dipakai:** rata-rata LightGBM + Logistik B (PR-AUC 0,658, brier 0,1345, hanya +0,002;
kerumitannya tidak sepadan).

Catatan: model apa pun di dataset ini kemungkinan mentok di kisaran yang sama karena hanya ±20 petunjuk per
pelanggan (tidak ada kualitas sinyal, tawaran kompetitor, keluhan, dan sebagainya). Lompatan besar terjadi dari
tebakan segmen ke model; selisih antar model hanya sisa.

## 6. Merapikan angka peluang

| Cara | PR-AUC | Rentang | Lift@10% | Brier |
|---|---|---|---|---|
| Tanpa perapian | 0,656 | 0,637 - 0,695 | 2,82 | 0,1348 |
| Sigmoid | 0,657 | 0,637 - 0,695 | 2,82 | 0,1348 |
| Isotonic | 0,652 | 0,610 - 0,678 | 2,77 | 0,1349 |

Aturan: perapian dipakai hanya kalau brier membaik **0,0005 atau lebih**. Tidak ada yang mencapainya
(sigmoid +0,0000, isotonic memburuk 0,0001 dan sedikit menurunkan urutan). Pengujian dilakukan berlapis
(pelurusan dipelajari hanya dari data belajar tiap putaran, diuji di kelompok yang belum dilihat).

**Keputusan: tidak perlu dirapikan.**

**Tabel peluang vs kenyataan, setelah sigmoid** (10 kelompok pelanggan, ±564 per kelompok):

| Kelompok | Prediksi | Kenyataan | Selisih |
|---|---|---|---|
| 1 (risiko terendah) | 0,017 | 0,011 | +0,006 |
| 2 | 0,028 | 0,018 | +0,010 |
| 3 | 0,048 | 0,041 | +0,007 |
| 4 | 0,083 | 0,101 | -0,018 |
| 5 | 0,144 | 0,151 | -0,007 |
| 6 | 0,228 | 0,234 | -0,006 |
| 7 | 0,323 | 0,314 | +0,009 |
| 8 | 0,454 | 0,442 | +0,012 |
| 9 | 0,586 | 0,591 | -0,005 |
| 10 (risiko tertinggi) | 0,745 | 0,750 | -0,005 |

Rata-rata semua kelompok: prediksi ≈ 0,266, kenyataan ≈ 0,265 (hitungan dari tabel). Selisih tidak condong
ke satu arah. Kelompok teratas, yang paling menentukan keputusan promo, hampir tepat.

**Tabel yang sama untuk model tanpa perapian (model yang benar-benar dipakai):** 
| Kelompok | Prediksi | Kenyataan | Selisih |
|---|---|---|---|
| 1 (risiko terendah) | 0,016 | 0,014 | +0,002 |
| 2 | 0,027 | 0,016 | +0,011 |
| 3 | 0,047 | 0,037 | +0,01 |
| 4 | 0,082 | 0,105 | -0,023 |
| 5 | 0,142 | 0,155 | -0,013 |
| 6 | 0,226 | 0,226 | 0,0 |
| 7 | 0,324 | 0,31 | +0,014 |
| 8 | 0,457 | 0,462 | -0,005 |
| 9 | 0,588 | 0,579 | 0,009 |
| 10 (risiko tertinggi) | 0,747 | 0,750 | -0,003 |

Kesimpulan "tidak perlu dirapikan" bertumpu pada brier (sigmoid tidak mengubah apa-apa), jadi tabel di atas
dicatat sebagai bukti tambahan, bukan dasar keputusan.

## 7. Uji fitur: dicabut satu per satu

Aturan: sebuah fitur boleh dicabut kalau ketepatan urutan turun **tidak lebih dari 0,002** dan brier
memburuk **tidak lebih dari 0,0005**. Kedua batas adalah aturan praktis, bukan standar baku.

**LightGBM** (basis: PR-AUC 0,656, brier 0,1348):

| Dicabut | PR-AUC | Perubahan rata-rata | Lift@10% | Brier |
|---|---|---|---|---|
| `charge_vs_hist` | 0,657 | +0,0009 | 2,83 | 0,1348 |
| `phone_service` | 0,655 | -0,0014 | 2,80 | 0,1350 |
| `multiple_lines` | 0,654 | -0,0018 | 2,80 | 0,1351 |
| Ketiganya | 0,655 | -0,0004 | 2,82 | 0,1350 |

**Logistik B** (basis: PR-AUC 0,645, brier 0,1365):

| Dicabut | PR-AUC | Perubahan rata-rata | Lift@10% | Brier |
|---|---|---|---|---|
| `charge_vs_hist` | 0,645 | +0,0007 | 2,78 | 0,1365 |
| `phone_service` | 0,643 | -0,0013 | 2,80 | 0,1367 |
| `multiple_lines` | 0,641 | -0,0018 | 2,77 | 0,1367 |

**Keputusan: cabut `charge_vs_hist` saja.**
- Mencabutnya tidak merugikan di kedua model.
- Ia turunan dari `total_charges` dan lama berlangganan, jadi tidak membawa informasi baru
  (sebelumnya ditandai "perlu uji" untuk kebocoran data; tidak ada indikasi bocor, AUC tunggal 0,506).
- `phone_service` dan `multiple_lines` secara aturan boleh dicabut, tetapi mencabutnya tidak memberi
  keuntungan, dan di dua model berbeda keduanya konsisten sedikit menurun (±0,0013 sampai 0,0018), yang
  mungkin menandakan sinyal kecil. Dipertahankan.

Semua selisih di atas jauh lebih kecil dari naik-turun antar-kelompok (±0,06). Data ini tidak bisa
membuktikan fitur mana yang penting; yang dipilih adalah opsi paling sederhana yang aman.

**Angka data belajar, konfigurasi final (tanpa `charge_vs_hist`, 22 fitur untuk LightGBM):**

| Model | PR-AUC | Rentang | Lift@10% | Brier |
|---|---|---|---|---|
| LightGBM final | 0,657 | 0,640 - 0,694 | 2,83 | 0,1348 |
| Logistik B final | 0,645 | 0,626 - 0,681 | 2,78 | 0,1365 |



## 8. Catatan tentang `phone_service`

Di model B, `phone_service` berbobot besar (-0,68) padahal tidak menonjol di EDA. Pemeriksaan di data belajar:

| Kelompok | Jumlah | Churn |
|---|---|---|
| Tanpa telepon (semuanya DSL) | 552 | 24,8% |
| DSL dengan telepon | 1.380 | 16,1% |
| Fiber (semuanya punya telepon) | 2.481 | 42,3% |
| Tanpa internet (semuanya punya telepon) | 1.221 | 7,1% |

- Semua pelanggan tanpa telepon memakai DSL, jadi fitur ini bercampur dengan jenis internet. Itu menjelaskan
  kenapa pengaruhnya tidak tampak di EDA (tertutup campuran fiber berisiko tinggi dan tanpa-internet berisiko rendah).
- Di dalam DSL, pelanggan tanpa telepon churn 24,8% vs 16,1%, selisih ±9 poin, tapi kontrak dan lama
  berlangganan belum dikendalikan.

## 9. Catatan jujur

- Pilihan pengaturan LightGBM (dari 5 opsi), pilihan `C`, dan pilihan fitur dibuat dari kelompok validasi yang
  sama dengan yang dipakai melapor. Angka data belajar mungkin sedikit **optimis**; angka resmi adalah angka
  ujian akhir.
- Satu putaran uji peluang dan uji fitur sempat menghasilkan angka LightGBM yang berbeda dari Step 9
  (PR-AUC 0,645 vs 0,656) dengan pengaturan yang seharusnya sama. Penyebabnya tidak diverifikasi (dugaan:
  pengaturan atau kode versi lama). Putaran ulang menghasilkan angka yang persis cocok dengan Step 9; angka
  putaran ulang yang dipakai di dokumen ini.
- Data snapshot: `tenure` dan `total_charges` pelanggan churn berhenti di titik kepergian, sedangkan pelanggan
  aktif terus berjalan. Tidak dapat diuji tanpa data bertanggal.
- Model memprediksi **siapa yang akan pergi**, bukan **siapa yang bisa dibujuk bertahan**. Save rate 25% adalah
  asumsi, divalidasi lewat A/B test (lihat rancangan eksperimen).
- `senior_citizen` dipertahankan sebagai fitur dan akan diaudit di akhir proyek (perbandingan tingkat
  penargetan antar kelompok). `gender` sengaja tidak dipakai.
- Dataset bergaya pascabayar; pasar Indonesia didominasi prabayar.

## 10. Sebelum ujian akhir (ditulis <tanggal>, SEBELUM test dibuka)

- **Model utama:** LightGBM, 300 pohon, 4 cabang, 22 fitur (tanpa `charge_vs_hist`)
- **Pembanding:** Logistik B (C = 0,3) dan tebakan segmen
- **Angka data belajar final:** LightGBM PR-AUC 0,657 / lift@10% 2,83 / brier 0,1348;
  Logistik B 0,645 / 2,78 / 0,1365
- **Tebakan hasil ujian:** PR-AUC LightGBM di kisaran **0,60 sampai 0,70** (data ujian lebih kecil, jadi lebih
  goyang; kisaran ini patokan kasar, bukan hasil perhitungan)
- **Aturan:** apa pun hasilnya, model utama tetap LightGBM dan **tidak ada penyetelan ulang** setelah melihat
  hasil. Satu-satunya pengecualian adalah bug teknis (misalnya kolom tertukar), yang harus dicatat
  alasannya di dokumen ini.
- **Tanda bahaya:** PR-AUC di atas 0,75 (curiga bocor) atau di bawah 0,55 (curiga rusak) → berhenti dan
  periksa sebelum melapor.
- **Ujian hanya dijalankan satu kali** (`python -m src.final_eval`, dengan "segel" `reports/test_results.json`).

## 11. Hasil ujian akhir (dibuka <tanggal>, 1.409 pelanggan, churn 26,5%)

| Model | PR-AUC [rentang 95%] | Lift@10% [rentang] | Brier [rentang] |
|---|---|---|---|
| Tebakan segmen | 0,527 [0,477-0,571] | 2,21 [2,00-2,61] | 0,1511 [0,1411-0,1605] |
| Logistik B | 0,682 [0,630-0,728] | 2,93 [2,61-3,27] | 0,1309 [0,1203-0,1412] |
| LightGBM | 0,686 [0,635-0,733] | 2,88 [2,62-3,26] | 0,1298 [0,1188-0,1400] |

Rentang 95% = acak ulang pelanggan ujian 1.000 kali; ini rentang goyangan, bukan jaminan.

- **Model vs tebakan segmen:** LightGBM +0,161 [0,122-0,203]; Logistik B +0,157 [0,114-0,202];
  menang di 100% acakan.
- **LightGBM vs Logistik B:** +0,005 [-0,015 sampai +0,025], lebih baik di 68% acakan. Rentang
  mencakup nol -> **setara**. LightGBM tetap model utama sesuai aturan yang ditulis sebelum ujian.
- **Daftar teratas (LightGBM):** menghubungi 20% teratas menangkap 51,6% churner (acak: 20%);
  10% teratas menangkap 28,6%; 50% teratas menangkap 88,8%.
- **Peluang vs kenyataan:** rata-rata prediksi 25,8% vs kenyataan 26,5%. Kelompok teratas:
  prediksi 74,0% vs kenyataan 76,6%. Di empat kelompok teratas prediksi cenderung sedikit di bawah
  kenyataan (1 sampai 3 poin), masih dalam batas kebetulan (±141 pelanggan per kelompok).
  Tidak dirapikan ulang sesuai aturan.
- **Dibanding tebakan sebelum ujian (PR-AUC 0,60-0,70):** sesuai (0,686). Tanda bahaya tidak terpicu.
- **Catatan:** angka ujian lebih tinggi dari angka validasi silang untuk semua model, termasuk
  tebakan segmen (+0,046), yang menunjukkan kelompok ujian kebetulan sedikit lebih mudah. Angka
  ujian dilaporkan sebagai angka resmi; selisih antar model lebih bisa dipercaya daripada angka mentahnya.
- **Tidak ada penyetelan ulang setelah ujian dibuka.**

## 12. Skor untuk Minggu 3 (`data/scored.parquet`)

Tujuan: peluang churn untuk semua 7.043 pelanggan yang **tidak pernah dilihat modelnya**, supaya hitungan uang
tidak terlalu optimis.

| Kelompok | Asal skor |
|---|---|
| Data belajar (5.634) | Validasi silang 5 kelompok: tiap pelanggan diskor oleh model yang tidak belajar dari kelompoknya (model dilatih pada 80% data belajar, ±4.507 pelanggan) |
| Data ujian (1.409) | Skor tersimpan dari ujian akhir (`data/test_pred.parquet`); model dilatih pada seluruh data belajar. **Tidak ada ujian ulang** |

Pemeriksaan (semua lolos):

| Cek | Hasil |
|---|---|
| Data belajar: PR-AUC / lift@10% / brier | 0,657 / 2,83 / 0,1348 (persis sama dengan Step 9 dan 10) |
| Data ujian: PR-AUC | 0,686 (persis sama dengan ujian akhir) |
| Rata-rata prediksi vs kenyataan | 0,264 vs 0,265 |
| Bentuk tabel | 7.043 baris, 18 kolom, ID unik, tidak ada nilai kosong, semua peluang di antara 0 dan 1 |

Perbedaan kecil yang diketahui: model untuk pelanggan data belajar dilatih pada 80% data belajar, sedangkan model
untuk pelanggan data ujian pada 100%. Dampaknya dianggap kecil dan tidak diukur.

## 13. Penjelasan model (SHAP)

Model yang dijelaskan = model yang sama dengan ujian akhir (dilatih pada data belajar), pada semua 7.043 pelanggan.
Cek penjumlahan (nilai dasar + poin risiko = keluaran model): selisih terbesar 7,5 × 10⁻¹⁵, jadi sah.

**Pengaruh rata-rata per fitur** (makin besar makin sering menggeser skor):

| Peringkat | Fitur | Pengaruh |
|---|---|---|
| 1 | contract | 0,612 |
| 2 | tenure_months | 0,401 |
| 3 | internet_service | 0,342 |
| 4 | is_echeck | 0,159 |
| 5 | total_charges | 0,128 |
| 6-11 | paperless_billing 0,120; n_streaming 0,119; is_month_to_month 0,116; monthly_charge 0,104; avg_monthly_hist 0,090; n_protection 0,088 | |

**Arah (rata-rata poin risiko per kategori):** kontrak bulanan +0,59, 1 tahun -0,27, 2 tahun -0,95; fiber +0,36,
DSL -0,17, tanpa internet -0,58. Sesuai temuan EDA untuk empat faktor teratas.

**Pelanggan contoh:** 5178-LMXOP (peluang 0,90): tenure 1 bulan (+0,93), bulanan (+0,71), fiber (+0,38), e-check
(+0,19), tanpa proteksi (+0,15). 2694-CIUMO (peluang 0,50): bulanan (+0,63) dan fiber (+0,43) menaikkan; bukan
e-check (-0,14) menurunkan.

**Hal yang perlu dicatat:**
- **Fitur kembar membagi pengaruh** (contract dan is_month_to_month; internet_service, is_fiber, has_internet;
  is_echeck dan payment_method). `payment_method` terlihat hampir nol (e-check hanya +0,04) karena pengaruhnya
  tercatat di `is_echeck`. Peringkat per fitur mengecilkan pengaruh gabungan sebuah informasi.
- **Perbedaan dari EDA:** `n_streaming` (0,119) lebih berpengaruh daripada `n_protection` (0,088), padahal di EDA
  streaming hampir tidak berhubungan dengan churn. Cek lanjutan pada pelanggan fiber dan bulanan (n = 2.128):

| Jumlah | Churn menurut proteksi | Churn menurut streaming |
|---|---|---|
| 0 | 65,2% (n = 814) | 52,5% (n = 793) |
| 1 | 53,1% (n = 737) | 54,1% (n = 673) |
| 2 | 45,4% (n = 432) | 57,7% (n = 662) |
| 3 | 30,2% (n = 126) | - |
| 4 | 31,6% (n = 19, terlalu sedikit) | - |

  Proteksi tetap menurunkan churn dalam kelompok yang sama; streaming tidak (malah sedikit naik, di perbatasan
  kebetulan). Penurunan ringan streaming di EDA sebagian adalah efek komposisi. Lama berlangganan dan tagihan
  belum dikendalikan. **Ini pengamatan tentang model, bukan temuan bisnis.**
- **Hampir tak berpengaruh:** has_partner (0,000), auto_pay (0,001), n_family (0,003), n_addons (0,011).
  Kandidat dicabut di versi berikutnya. **Tidak diubah sekarang** karena data ujian sudah terpakai.
- Peringatan dari `shap` soal format keluaran (daftar `ndarray`) tidak berbahaya; kode menangani kedua format.

Keputusan turunan: untuk mengukur keterlibatan pelanggan di segmentasi (Step 16), pakai **jumlah proteksi**,
bukan total add-on.

## 14. Audit kelompok lansia (pada `scored.parquet`)

| Kelompok | Jumlah | Prediksi | Kenyataan | Selisih | Di 20% skor teratas |
|---|---|---|---|---|---|
| Non-lansia | 5.901 | 23,8% | 23,6% | +0,2 poin | 17,0% |
| Lansia | 1.142 | 39,9% | 41,7% | -1,8 poin | 35,6% |

- Prediksi akurat di kedua kelompok; pada lansia sedikit **konservatif** (meremehkan risiko 1,8 poin, dalam batas
  kebetulan untuk n = 1.142).
- Lansia 16,2% dari pelanggan, tetapi ±29% dari kelompok skor teratas (2,1 kali lebih sering terpilih, sementara
  churn mereka 1,8 kali lebih tinggi). Sejalan dengan perbedaan risiko dasar; penyebab selisih kecil antara 2,1 dan
  1,8 tidak diselidiki.
- Batas pemeriksaan: hanya akurasi prediksi per kelompok dan tingkat keterpilihan untuk satu atribut. **Bukan
  jaminan keadilan.** Dampak promo pada kelompok ini diperiksa lagi saat daftar target terbentuk (Step 16).
- **Tidak ada perubahan model berdasarkan hasil ini.**

## 15. Lapisan nilai bisnis (`src/value.py`)

Semua asumsi dikumpulkan di `Params` (nilai awal sama dengan `docs/assumptions.md`):

| Parameter | Nilai |
|---|---|
| Margin kontribusi | 40% |
| Horizon | 12 bulan |
| Save rate (promo menahan calon churner) | 25% (**asumsi**, belum dibuktikan) |
| Biaya kontak | Rp 2.000 per orang |
| Biaya insentif | Rp 10.000 per penerima |
| Take-up insentif | 30% |
| Biaya efektif per orang yang dihubungi | Rp 5.000 (2.000 + 0,3 × 10.000) |

```
nilai pelanggan (CLV) = tagihan bulanan × margin × horizon
untung bersih diharapkan (EV) = peluang pergi × save rate × CLV − biaya efektif
titik impas peluang = biaya efektif ÷ (save rate × CLV)
```

Hitungan tangan lolos (tagihan Rp 46.000, peluang 50%): CLV Rp 220.800; nilai diselamatkan Rp 27.600;
EV Rp 22.600; titik impas 9,1%.

**Hasil pada 7.043 pelanggan:**

| Hasil | Nilai |
|---|---|
| CLV rata-rata | Rp 220.800 |
| Titik impas peluang | rata-rata 12,8%, tengah 8,3%, rentang 4,9% sampai 32,1% |
| Pelanggan dengan EV > 0 | 4.195 dari 7.043 (59,6%) |
| Biaya menghubungi semua | Rp 35.215.000 |
| Biaya menghubungi yang layak saja | Rp 20.975.000 |
| Total untung bersih diharapkan (EV > 0) | Rp 92.367.154 (**di bawah asumsi save rate 25%**) |

**Layak dihubungi menurut kelompok:** kontrak bulanan 85,7% (n = 3.875); 1 tahun 44,8% (n = 1.473); 2 tahun 12,7%
(n = 1.695, sekitar 215 orang layak karena tagihan besar dan peluang pergi relatif tinggi, yang tidak bisa
ditemukan tebakan segmen). Lansia 83,8% (n = 1.142) vs non-lansia 54,9%.

**Dibanding EV kasar di EDA:** hampir sama untuk segmen bulanan dan 2 tahun. Dua perbedaan:
- Bulanan 48+ bulan: EV naik dari 14.765 ke 19.026 karena model terlalu pesimis di segmen ini (prediksi 30,9% vs
  kenyataan 25,8%, n = 357). Untung segmen ini mungkin dilebih-lebihkan. Model tidak diubah.
- Segmen 1 tahun berada di sekitar titik impas dan kecil (n = 32 sampai 199); tanda untung-rugi berbalik untuk
  12-23 bulan (+1.014 menjadi -861) dan 0-5 bulan (+721 menjadi -1.472). **Tidak dijadikan kesimpulan per segmen.**

**Asumsi struktural baru:**
- Pelanggan yang diselamatkan diasumsikan bertahan penuh 12 bulan dengan margin tetap (tanpa diskon waktu dan tanpa
  risiko pergi lagi). Arahnya bisa menaikkan atau menurunkan nilai.
- Budget = pengeluaran yang diharapkan (biaya kontak + take-up × insentif), bukan pengeluaran pasti.
- Skor model sedikit konservatif di kelompok teratas (1-3 poin pada ujian akhir), sehingga untung diharapkan
  cenderung sedikit diremehkan.
- Skala budget: **Opsi A**, rentang disesuaikan dengan ukuran dataset (±Rp 1 juta sampai 40 juta). Menarget semua
  = Rp 35,2 juta.

## 16. Perbandingan strategi pada budget yang sama (`src/strategies.py`)

| Cara | Memilih siapa |
|---|---|
| Acak | Nilai rata-rata dari semua kemungkinan undian acak (tanpa goyangan undian) |
| Urut risiko | Peluang pergi tertinggi dulu (tanpa rem; bisa menghubungi yang rugi) |
| Urut untung | EV tertinggi dulu, **berhenti bila EV ≤ 0** |

"Hubungi semua" bukan cara terpisah; itu ujung kurva acak pada budget Rp 35,2 juta.

**Dua cara menilai:** (1) *perkiraan model* (EV dari peluang model; "urut untung" pasti menang di sini, jadi
bukan bukti), (2) *kenyataan di data* (pelanggan yang benar-benar pergi × save rate × CLV − biaya; tidak bergantung
pada angka peluang model, tetapi **masih memakai asumsi save rate yang sama**).

Pemeriksaan lolos: dua cara hitung (`curve` dan `select_targets`) cocok; pada budget penuh, "urut untung" =
4.195 orang, biaya Rp 20.975.000, perkiraan Rp 92.367.154 (sama dengan bagian 15).

**Untung bersih menurut kenyataan di data (Rp juta):**

| Budget | Acak | Urut risiko | Urut untung |
|---|---|---|---|
| Rp 5 juta | 11,8 | 45,1 | **47,7** |
| Rp 10 juta | 23,7 | 72,2 | **74,7** |
| Rp 15 juta | 35,5 | 85,0 | **88,0** |
| Rp 21 juta | 49,7 | 90,9 | **92,7** |
| Rp 35,2 juta (semua) | 83,4 | 83,4 | **92,7** |

Perkiraan model nyaris sama dengan kenyataan (misalnya Rp 92,4 vs 92,7 juta untuk "urut untung" pada budget
penuh), jadi peluang model tidak menyesatkan hitungan uang.

**Seberapa pasti selisihnya** (acak ulang pelanggan 500 kali; rentang ini hanya mencakup goyangan sampel
pelanggan, bukan ketidakpastian save rate):

| Perbandingan | Budget | Selisih untung | Rentang 95% |
|---|---|---|---|
| Urut untung vs urut risiko | Rp 10 juta | +Rp 2,39 juta | +0,95 sampai +3,86 |
| Urut untung vs urut risiko | Rp 21 juta | +Rp 1,68 juta | +0,75 sampai +2,75 |
| Urut untung vs acak | Rp 10 juta | +Rp 51,0 juta | +48,5 sampai +53,6 |
| Urut untung vs acak | Rp 21 juta | +Rp 42,9 juta | +41,1 sampai +44,9 |
| Hubungi yang layak vs hubungi semua | Rp 35,2 juta | +Rp 9,27 juta | +8,36 sampai +10,14 |

**Kesimpulan yang boleh diklaim (di bawah asumsi save rate 25%):**
1. Memilih pelanggan jauh lebih untung daripada acak (±3,2 kali pada Rp 10 juta; ±4 kali pada Rp 5 juta).
2. **Berhenti di waktu yang tepat adalah penghematan terbesar:** menghubungi hanya yang layak menghasilkan
   Rp 92,7 juta dengan biaya Rp 21,0 juta, dibanding Rp 83,4 juta dengan biaya Rp 35,2 juta (selisih biaya
   Rp 14,2 juta; untung bersih per Rp 1 biaya ±4,4 vs ±2,4). Pelanggan yang layak mencakup 1.714 dari 1.869
   pelanggan yang akhirnya pergi (91,7%).
3. "Urut untung" lebih baik dari "urut risiko", tetapi **kecil** (±2 sampai 6%): nyata menurut rentang 95%,
   namun tidak besar. Selisih terbesar ada pada rem "berhenti bila EV ≤ 0".
4. Menambah budget makin tidak menguntungkan: tambahan untung Rp 27,0 juta (5→10), Rp 13,3 juta (10→15),
   Rp 4,7 juta (15→21), dan Rp 0 di atas ±Rp 21 juta.
5. "Urut risiko" menangkap lebih banyak pelanggan yang pergi (1.213 vs 1.161 pada Rp 10 juta) tetapi
   menghasilkan lebih sedikit uang: pelanggan paling berisiko belum tentu yang paling layak diselamatkan.

**Pemeriksaan hanya data ujian (1.409 pelanggan; untung menurut kenyataan, Rp juta):**

| Budget | Acak | Urut risiko | Urut untung |
|---|---|---|---|
| Rp 1,0 juta | 2,31 | 9,34 | 9,64 |
| Rp 2,0 juta | 4,62 | 14,66 | 14,68 |
| Rp 3,0 juta | 6,92 | 16,92 | 17,22 |
| Rp 4,2 juta | 9,69 | 17,80 | 18,00 |
| Rp 7,0 juta (semua) | 16,26 | 16,26 | 18,00 |

Arah sama dengan hasil seluruh pelanggan. Selisih "untung" vs "risiko" pada budget kecil (Rp 0,02 sampai 0,30 juta)
terlalu kecil untuk dibedakan pada data sekecil ini; efek berhenti di waktu yang tepat konsisten (Rp 18,0 vs
16,3 juta pada budget penuh).

## 17. Catatan jujur tambahan

- **Semua angka rupiah adalah perkiraan di bawah asumsi save rate 25%**, yang belum dibuktikan A/B test. Tulis
  sebagai "di bawah asumsi ..., perkiraan untung bersih Rp X juta", bukan "proyek ini menghasilkan Rp X juta".
- "Kenyataan di data" membuktikan **siapa yang pergi**, bukan **siapa yang bisa dibujuk bertahan**. Model memprediksi
  churn, bukan efek promo.
- Perbandingan strategi memakai seluruh 7.043 pelanggan; skor pelanggan data belajar berasal dari validasi silang
  yang pengaturannya dipilih dari kelompok yang sama, jadi masih ada sedikit optimisme.
- Rentang 95% pada bagian 16 hanya mencakup variasi sampel pelanggan. Ketidakpastian asumsi (save rate, biaya,
  margin) diuji terpisah di Step 15.
- Angka rupiah memakai ARPU blended Rp 46.000 (bukan ARPU pascabayar), yang mungkin mengecilkan CLV.
- Dataset bergaya pascabayar; pasar Indonesia didominasi prabayar.

## 18. Belum dilakukan

- [ ] Uji kepekaan: save rate, biaya, margin, ARPU; titik impas save rate (Step 15)
- [ ] Segmentasi nilai × keterlibatan (pakai jumlah proteksi) dan jenis promo; cek lansia pada daftar target (Step 16)
- [ ] Rancangan A/B test (Step 17)
- [ ] Aplikasi Streamlit, README, video demo, dan keputusan file data yang boleh dipublikasikan beserta cek
      lisensi dataset (Minggu 4)