# Asumsi Bisnis & Definisi

> Ditulis SEBELUM eksplorasi data. Semua angka adalah asumsi awal yang
> akan diuji sensitivitasnya, bukan fakta operator.

## 1. Konteks keputusan
- **Pengambil keputusan:** Tim Retention/CRM
- **Keputusan:** Pelanggan mana yang menerima promo retensi bulan ini,
  dengan batas budget tertentu
- **Metrik sukses:** Net value (nilai yang diselamatkan − biaya kampanye)
- **Bukan metrik sukses:** Akurasi model, jumlah churner yang terdeteksi

## 2. Definisi
| Istilah | Definisi |
|---|---|
| Churn | Churn menggambarkan kondisi ketika pelanggan berhenti berlangganan atau berhenti menggunakan layanan bisnis dalam jangka waktu tertentu. Istilah ini umum digunakan dalam bisnis berbasis langganan, SaaS, telekomunikasi, dan layanan digital. |
| Pelanggan "diselamatkan" | Calon churner yang tetap berlangganan setelah promo |
| CLV | Margin kontribusi bulanan × horizon (bukan revenue) |

## 3. Parameter bisnis
| Parameter | Nilai awal | Rentang uji | Alasan | Sumber / status |
|---|---|---|---|---|
| Margin kontribusi | 40% | 20-60% | Ini bukan margin laba resmi | asumsi kerja, bukan data internal operator |
| Horizon CLV (bulan) | 12 bulan |6 - 24 | horizon pendek lebih konservatif, dan lifetime tak terbatas hampir selalu melebih-lebihkan nilai | Asumsi kerja (judgment) |
| Save rate | 25% | 10 - 40 % | parameter paling menentukan dan paling tidak pasti | asumsi; divalidasi lewat A/B test |
| Biaya kontak per target (Rp) | Rp 2.000 | Rp 500 - 5.000 | Campuran kanal: mayoritas SMS/push/in-app (murah), sebagian kecil panggilan keluar (mahal). Nilai ini rata-rata tertimbang. | Asumsi kerja (judgment), bukan data operator. |
| Biaya insentif per penerima (Rp) | Rp 10.000 | Rp 5.000 - 20.000 | Setara ±20% dari ARPU bulanan, bentuknya diskon sekali pakai. | Asumsi kerja (judgment). |
| Target ARPU untuk rescale (Rp/bulan) | Rp 46.000 | Rp 45.000 - 150.000 | Satu-satunya angka publik yang terverifikasi. Rentang atas adalah proksi bahwa pascabayar lebih tinggi dari blended | Telkom public expose, ARPU Q2-2026 (kabarbursa.com, 7 Sep 2026). Blended, bukan pascabayar saja. Batas atas rentang adalah judgment. |

## 4. Asumsi struktural (yang paling berisiko)
1. Save rate sama untuk semua pelanggan → disederhanakan; kenyataannya
   berbeda per segmen (ditangani lewat uplift modeling sebagai next step)
2. Pelanggan non-churn yang menerima promo ikut menikmati diskon →
   masuk ke komponen biaya
3. Tidak ada efek interaksi antar kampanye
4. Data adalah snapshot, tanpa dimensi waktu

## 5. Limitasi yang sudah diketahui sejak awal
- Dataset bergaya pascabayar; pasar Indonesia didominasi prabayar
- Mata uang dataset bukan rupiah, perlu rescale
- (tambahkan di Step 6 jika ada temuan baru)

## 6. Changelog asumsi
| Tanggal | Perubahan | Alasan |
|7 Oktober 2026|Biaya Rp 15.000 gelondongan diganti kontak + insentif + take-up|Lebih realistis, komponen bisa diuji sensitivitasnya terpisah|

Lisensi: sumber resmi repo IBM telco-customer-churn-on-icp4d (Apache 2.0, diakses 24 Oktober 2026); Kaggle hanya salinan. Data turunan minimal dipublikasikan dengan atribusi dan pernyataan perubahan (lihat NOTICE).