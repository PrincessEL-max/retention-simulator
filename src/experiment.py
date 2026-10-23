# src/experiment.py
import numpy as np
from statsmodels.stats.power import NormalIndPower
from statsmodels.stats.proportion import proportion_effectsize

Z = 1.96


def n_kontrol(churn_kontrol, save_rate, share_kontrol=0.5, alpha=0.05, power=0.8):
    """Jumlah pelanggan di kontrol dan di promo agar save rate tertentu terdeteksi."""
    p_promo = churn_kontrol * (1 - save_rate)
    h = proportion_effectsize(churn_kontrol, p_promo)
    rasio = (1 - share_kontrol) / share_kontrol
    n_c = NormalIndPower().solve_power(effect_size=h, alpha=alpha, power=power,
                                       ratio=rasio, alternative="two-sided")
    return int(np.ceil(n_c)), int(np.ceil(n_c * rasio))


def baca_hasil(x_c, n_c, x_t, n_t, break_even=0.046):
    """x = jumlah yang churn, n = jumlah pelanggan. c = kontrol, t = promo."""
    if x_c == 0 or x_t == 0:
        return dict(save=np.nan, lo=np.nan, hi=np.nan, keputusan="belum jelas")
    rr = (x_t / n_t) / (x_c / n_c)
    se = np.sqrt(1 / x_t - 1 / n_t + 1 / x_c - 1 / n_c)
    lo, hi = 1 - rr * np.exp(Z * se), 1 - rr * np.exp(-Z * se)
    keputusan = "lanjutkan" if lo > break_even else "hentikan" if hi < break_even else "belum jelas"
    return dict(save=1 - rr, lo=lo, hi=hi, keputusan=keputusan)


def simulasi(churn_nyata, save_rate_benar, n_ulang=1000, share_kontrol=0.5,
             break_even=0.046, seed=42):
    """Anggap pelanggan yang churn di data = calon churner tanpa promo.
    Promo menyelamatkan tiap calon churner dengan peluang save_rate_benar."""
    rng = np.random.default_rng(seed)
    y = np.asarray(churn_nyata).astype(int)
    hasil = {"lanjutkan": 0, "hentikan": 0, "belum jelas": 0}
    est = []
    for _ in range(n_ulang):
        kontrol = rng.random(len(y)) < share_kontrol
        selamat = rng.random(len(y)) < save_rate_benar
        y_promo = y * (~selamat)
        r = baca_hasil(y[kontrol].sum(), kontrol.sum(),
                       y_promo[~kontrol].sum(), (~kontrol).sum(), break_even)
        hasil[r["keputusan"]] += 1
        est.append(r["save"])
    return {k: v / n_ulang for k, v in hasil.items()}, float(np.nanmean(est))