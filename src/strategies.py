# src/strategies.py
import numpy as np
import pandas as pd
from src.value import Params

LABEL = {"acak": "Pilih acak",
         "risiko": "Urut risiko tertinggi",
         "untung": "Urut untung tertinggi"}


def _nilai_nyata(v, p):
    """Nilai yang terselamatkan jika promo berhasil, hanya untuk yang memang pergi (sebelum biaya)."""
    return (v["churned"] * p.save_rate * v["clv"]).to_numpy()


def curve(v, p, budgets):
    """Untung bersih tiap cara pada tiap budget. v = tabel dari add_value()."""
    N, cost = len(v), p.eff_cost
    ev = v["ev"].to_numpy()
    nyata = _nilai_nyata(v, p)
    pergi = v["churned"].to_numpy().astype(float)
    peluang = v["p_churn"].to_numpy()

    urut_risiko = np.argsort(-peluang, kind="stable")
    urut_untung = np.argsort(-ev, kind="stable")
    n_layak = int((ev > 0).sum())

    def jumlah_berjalan(a, urutan):
        # elemen ke-n = jumlah nilai dari n orang pertama
        return np.concatenate([[0.0], np.cumsum(a[urutan])])

    cara = {"risiko": (urut_risiko, N), "untung": (urut_untung, n_layak)}
    tabel = {k: (jumlah_berjalan(ev, o), jumlah_berjalan(nyata, o), jumlah_berjalan(pergi, o))
             for k, (o, _) in cara.items()}

    rows = []
    for b in budgets:
        n_budget = min(N, int(b // cost))
        # Acak: nilai rata-rata dari semua kemungkinan acakan (dihitung langsung)
        rows.append(dict(strategi="acak", budget=b, n=n_budget,
                         perkiraan=n_budget * ev.mean(),
                         kenyataan=n_budget * (nyata.mean() - cost),
                         churner=n_budget * pergi.mean()))
        for k, (_, n_max) in cara.items():
            n = min(n_budget, n_max)
            ev_kum, nyata_kum, pergi_kum = tabel[k]
            rows.append(dict(strategi=k, budget=b, n=n,
                             perkiraan=ev_kum[n],
                             kenyataan=nyata_kum[n] - n * cost,
                             churner=pergi_kum[n]))
    out = pd.DataFrame(rows)
    out["biaya"] = out["n"] * cost
    return out


def select_targets(v, budget, p, strategi="untung", seed=42):
    """Daftar pelanggan yang dihubungi (dipakai juga oleh aplikasi nanti)."""
    n_budget = min(len(v), int(budget // p.eff_cost))
    if strategi == "untung":
        s = v[v["ev"] > 0].sort_values("ev", ascending=False, kind="stable").head(n_budget)
    elif strategi == "risiko":
        s = v.sort_values("p_churn", ascending=False, kind="stable").head(n_budget)
    else:
        s = v.sample(n=n_budget, random_state=seed)
    n = len(s)
    nyata = (s["churned"] * p.save_rate * s["clv"]).sum() - n * p.eff_cost
    return s, {"n": n, "biaya": n * p.eff_cost,
               "perkiraan": s["ev"].sum(), "kenyataan": nyata,
               "churner": int(s["churned"].sum()),
               "persen_churner": s["churned"].sum() / v["churned"].sum()}


def bootstrap_selisih(v, p, budget, n_ulang=500, seed=42):
    """Acak ulang daftar pelanggan n_ulang kali (boleh terpilih dua kali), lalu hitung selisih
    untung 'untung' vs 'risiko' dan vs 'acak'. Hasil: (rata-rata, batas bawah, batas atas 95%)."""
    rng = np.random.default_rng(seed)
    a, b = [], []
    for _ in range(n_ulang):
        s = v.iloc[rng.integers(0, len(v), len(v))]
        c = curve(s, p, [budget]).set_index("strategi")["kenyataan"]
        a.append(c["untung"] - c["risiko"])
        b.append(c["untung"] - c["acak"])
    f = lambda x: (float(np.mean(x)), float(np.percentile(x, 2.5)), float(np.percentile(x, 97.5)))
    return {"untung vs risiko": f(a), "untung vs acak": f(b)}