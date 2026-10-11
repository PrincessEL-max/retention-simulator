# src/cv.py
import numpy as np
from src.features import TARGET
from src.metrics import summary
from sklearn.metrics import average_precision_score

def cv_oof(dev, fit_predict):
    """fit_predict(train_df, valid_df) -> peluang untuk valid_df."""
    oof = np.zeros(len(dev))
    for k in sorted(dev["fold"].unique()):
        tr = dev[dev["fold"] != k]
        va = dev[dev["fold"] == k]
        oof[va.index] = fit_predict(tr, va)
    return oof

def report(dev, oof, name):
    s = summary(dev[TARGET], oof)
    per_fold = [
        average_precision_score(dev.loc[dev.fold == k, TARGET], oof[dev.fold == k])
        for k in sorted(dev["fold"].unique())
    ]
    print(f"{name:28s} PR-AUC {s['pr_auc']:.3f} "
          f"(antar-lipatan {min(per_fold):.3f}-{max(per_fold):.3f}) | "
          f"lift@10% {s['lift@10%']:.2f} | brier {s['brier']:.4f}")
    return s

def compare_folds(dev, oof_new, oof_old, name_new="baru", name_old="lama"):
    """Bandingkan dua model kelompok demi kelompok (ketepatan urutan)."""
    wins = 0
    for k in sorted(dev["fold"].unique()):
        m = (dev["fold"] == k).values
        a = average_precision_score(dev.loc[m, TARGET], oof_new[m])
        b = average_precision_score(dev.loc[m, TARGET], oof_old[m])
        wins += int(a > b)
        print(f"kelompok {k}: {name_new} {a:.3f} vs {name_old} {b:.3f}  "
              f"{'menang' if a > b else 'kalah'}")
    print(f"=> {name_new} menang di {wins} dari 5 kelompok")
    return wins

def fold_ap(dev, oof):
    """Ketepatan urutan per kelompok."""
    return np.array([
        average_precision_score(dev.loc[dev.fold == k, TARGET], oof[(dev.fold == k).values])
        for k in sorted(dev["fold"].unique())
    ])