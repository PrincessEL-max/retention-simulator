# src/sensitivity.py
from dataclasses import replace
import numpy as np
import pandas as pd
from src.value import Params, add_value


def hasil(sc, p, arpu_faktor=1.0):
    """Pilih pelanggan EV > 0 menurut asumsi p, lalu hitung untungnya."""
    d = sc.assign(monthly_charge=sc["monthly_charge"] * arpu_faktor)
    v = add_value(d, p)
    s = v[v["ev"] > 0]
    n = len(s)
    return {"n": n, "biaya": n * p.eff_cost, "perkiraan": s["ev"].sum(),
            "kenyataan": (s["churned"] * p.save_rate * s["clv"]).sum() - n * p.eff_cost}


# Rentang uji dari docs/assumptions.md
RENTANG = {"save rate": ("save_rate", 0.10, 0.40),
           "margin": ("margin", 0.20, 0.60),
           "horizon (bulan)": ("horizon", 6, 24),
           "biaya kontak": ("contact_cost", 500, 5_000),
           "biaya insentif": ("incentive_cost", 5_000, 20_000),
           "take-up": ("takeup", 0.15, 0.50)}


def tornado(sc, P):
    dasar = hasil(sc, P)["kenyataan"]
    rows = []
    for nama, (f, lo, hi) in RENTANG.items():
        r = [hasil(sc, replace(P, **{f: x}))["kenyataan"] for x in (lo, hi)]
        rows.append({"parameter": nama, "rendah": r[0], "tinggi": r[1]})
    r = [hasil(sc, P, arpu_faktor=x / 46_000)["kenyataan"] for x in (45_000, 150_000)]
    rows.append({"parameter": "ARPU (Rp 45 rb - 150 rb)", "rendah": r[0], "tinggi": r[1]})
    t = pd.DataFrame(rows)
    t["lebar"] = (t["tinggi"] - t["rendah"]).abs()
    return dasar, t.sort_values("lebar", ascending=False).reset_index(drop=True)


def peta(sc, P, save_rates, biaya, kolom="kenyataan"):
    """Tabel save rate x biaya efektif per orang."""
    out = pd.DataFrame(index=biaya, columns=save_rates, dtype=float)
    for c in biaya:
        for s in save_rates:
            q = replace(P, save_rate=s, contact_cost=c, incentive_cost=0, takeup=0)
            out.loc[c, s] = hasil(sc, q)[kolom]
    return out


def ketahanan(sc, P, save_rates):
    """Daftar target dipilih pada asumsi awal. Bagaimana jika save rate sebenarnya berbeda?"""
    base = add_value(sc, P)
    pilih = base[base["ev"] > 0]
    c = P.eff_cost
    rows = []
    for s in save_rates:
        rows.append({"save_rate_sebenarnya": s,
                     "hubungi_semua": (base["churned"] * s * base["clv"]).sum() - len(base) * c,
                     "daftar_asumsi_awal": (pilih["churned"] * s * pilih["clv"]).sum() - len(pilih) * c,
                     "daftar_dipilih_ulang": hasil(sc, replace(P, save_rate=s))["kenyataan"]})
    return pd.DataFrame(rows)


def titik_impas(sc, P):
    """Save rate minimum agar untung bersih = 0 (menurut kenyataan di data)."""
    base = add_value(sc, P)
    pilih = base[base["ev"] > 0]
    c = P.eff_cost
    return {"hubungi_semua": len(base) * c / (base["churned"] * base["clv"]).sum(),
            "daftar_asumsi_awal": len(pilih) * c / (pilih["churned"] * pilih["clv"]).sum()}