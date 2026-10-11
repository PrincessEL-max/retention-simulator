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
