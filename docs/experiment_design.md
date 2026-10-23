## Ukuran sampel
Untuk mendeteksi save rate tertentu (alpha 5%, power 80%, churn dasar 40,9%, dibanding nol):

| Save rate | Porsi kontrol | Kontrol | Promo | Total | Untung tertahan (Rp juta) |
|---|---|---|---|---|---|
| 25% | 50% | 344 | 344 | 688 | 7,6 |
| 20% | 50% | 545 | 545 | 1.090 | 12,0 |
| 15% | 50% | 981 | 981 | 1.962 | 21,6 |
| 15% | 30% | 701 | 1.635 | 2.336 | 15,4 |
| 10% | 50% | 2.232 | 2.232 | 4.464 | tidak muat di 4.195 |

Aturan keputusan (batas bawah 95% > 4,6%) lebih ketat daripada deteksi dibanding nol, sehingga butuh
sampel lebih besar daripada tabel di atas.

## Simulasi pada data kita (4.195 pelanggan, bagi 50:50, 1.000 ulangan)
| Save rate sebenarnya | Lanjutkan | Hentikan | Belum jelas |
|---|---|---|---|
| 0% | 0% | 26% | 74% |
| 4,6% | 2% | 3% | 95% |
| 10% | 32% | 0% | 68% |
| 15% | 82% | 0% | 18% |
| 25% | 100% | 0% | 0% |

Uji ini hanya memberi jawaban jelas jika save rate ≥ 15%. Di kisaran 5-10% dibutuhkan basis pelanggan
jauh lebih besar. Pembagian 30% kontrol belum disimulasikan.