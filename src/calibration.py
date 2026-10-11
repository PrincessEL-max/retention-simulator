# src/calibration.py
import numpy as np
from sklearn.model_selection import StratifiedKFold
from sklearn.linear_model import LogisticRegression
from sklearn.isotonic import IsotonicRegression
from src.features import TARGET

def _logit(p):
    p = np.clip(p, 1e-4, 1 - 1e-4)
    return np.log(p / (1 - p)).reshape(-1, 1)

class Calibrator:
    """method = 'sigmoid' atau 'isotonic'"""
    def __init__(self, method="sigmoid"):
        self.method = method

    def fit(self, p, y):
        if self.method == "sigmoid":
            self.m = LogisticRegression(C=1e6, max_iter=1000).fit(_logit(p), y)
        else:
            self.m = IsotonicRegression(out_of_bounds="clip", y_min=0, y_max=1).fit(p, y)
        return self

    def predict(self, p):
        if self.method == "sigmoid":
            return self.m.predict_proba(_logit(p))[:, 1]
        return self.m.predict(p)

def _inner_oof(tr, fit_predict, n_splits=5, seed=42):
    tr = tr.reset_index(drop=True)
    oof = np.zeros(len(tr))
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    for a, b in skf.split(tr, tr[TARGET]):
        oof[b] = fit_predict(tr.iloc[a], tr.iloc[b])
    return tr, oof

def cv_oof_calibrated(dev, fit_predict, method):
    out = np.zeros(len(dev))
    for k in sorted(dev["fold"].unique()):
        tr = dev[dev["fold"] != k]
        va = dev[dev["fold"] == k]
        tr, p_inner = _inner_oof(tr, fit_predict)                     # prediksi "jujur" di data belajar
        cal = Calibrator(method).fit(p_inner, tr[TARGET].values)      # pelurusan dipelajari di sini
        out[va.index] = cal.predict(fit_predict(tr, va))              # diuji di kelompok yang belum dilihat
    return out