# src/metrics.py
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

