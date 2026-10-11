# src/metrics.py
import pandas as pd
import numpy as np
from sklearn.metrics import (average_precision_score, roc_auc_score,
                             brier_score_loss, log_loss)

def lift_at(y, p, frac=0.10):
    """Berapa kali lebih banyak churner di 10% skor tertinggi dibanding acak."""
    y, p = np.asarray(y), np.asarray(p)
    n = int(len(p) * frac)
    top = np.argsort(-p)[:n]
    return y[top].mean() / y.mean()

def summary(y, p):
    return {
        "pr_auc": average_precision_score(y, p),
        "roc_auc": roc_auc_score(y, p),
        "lift@10%": lift_at(y, p, 0.10),
        "lift@20%": lift_at(y, p, 0.20),
        "brier": brier_score_loss(y, np.clip(p, 0, 1)),
        "logloss": log_loss(y, np.clip(p, 1e-6, 1 - 1e-6)),
    }

def reliability(y, p, bins=10):
    d = pd.DataFrame({"y": np.asarray(y), "p": np.asarray(p)})
    d["kelompok"] = pd.qcut(d["p"], bins, duplicates="drop")
    t = d.groupby("kelompok", observed=True).agg(
        n=("y", "size"), rata_prediksi=("p", "mean"), kenyataan=("y", "mean")).round(3)
    t["selisih"] = (t["rata_prediksi"] - t["kenyataan"]).round(3)
    return t

def gain_table(y, p, fracs=(0.1, 0.2, 0.3, 0.4, 0.5)):
    """Kalau hanya menghubungi X% teratas, berapa persen churner yang tertangkap?"""
    y, p = np.asarray(y), np.asarray(p)
    order = np.argsort(-p)
    rows = []
    for f in fracs:
        n = int(len(p) * f)
        rows.append({"hubungi_teratas": f"{int(f * 100)}%",
                     "churner_tertangkap": round(y[order[:n]].sum() / y.sum(), 3),
                     "kalau_acak": f})
    return pd.DataFrame(rows)
