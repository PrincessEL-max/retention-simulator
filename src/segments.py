# src/segments.py
import numpy as np
import pandas as pd

URUT = ["Tanpa internet", "Proteksi 0", "Proteksi 1-2", "Proteksi 3-4"]

def tambah_segmen(v):
    d = v.copy()
    d["keterlibatan"] = np.select(
        [d["internet_service"] == "No", d["n_protection"] == 0, d["n_protection"] <= 2],
        ["Tanpa internet", "Proteksi 0", "Proteksi 1-2"],
        default="Proteksi 3-4")
    return d

def ringkas_segmen(v, P):
    """v = tabel dari add_value(). Untung dihitung hanya untuk pelanggan layak (EV > 0)."""
    d = tambah_segmen(v)
    d["layak"] = d["ev"] > 0
    d["ev_layak"] = np.where(d["layak"], d["ev"], 0.0)
    d["nyata_layak"] = np.where(
        d["layak"], d["churned"] * P.save_rate * d["clv"] - P.eff_cost, 0.0)
    t = (d.groupby(["monthly_charge_band", "keterlibatan"])
           .agg(n=("ev", "size"), churn=("churned", "mean"), p_rata=("p_churn", "mean"),
                layak=("layak", "mean"), ev_layak=("ev_layak", "sum"),
                nyata_layak=("nyata_layak", "sum"))
           .reset_index())
    t["porsi_untung"] = t["nyata_layak"] / t["nyata_layak"].sum()
    t["ev_layak"] /= 1e6
    t["nyata_layak"] /= 1e6
    t["kecil"] = t["n"] < 100
    return t.round(3)