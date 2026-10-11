# src/models_gbm.py
import pandas as pd
import lightgbm as lgb
from src.features import TARGET, EXCLUDE

CAT_GBM = ["contract", "payment_method", "internet_service"]

# Tidak dipakai: ID, target, band tagihan, kelompok CV, dan tenure_bucket
# (tenure_bucket hanya versi "dibulatkan" dari tenure_months)
DROP_GBM = EXCLUDE + ["tenure_bucket", "fold", "charge_vs_hist"]

def get_categories(df):
    """Catat daftar kategori dari data belajar (dipakai juga untuk data ujian nanti)."""
    return {c: sorted(df[c].unique()) for c in CAT_GBM}

def apply_categories(df, cats):
    d = df.copy()
    for c, levels in cats.items():
        d[c] = pd.Categorical(d[c], categories=levels)
    return d

def gbm_columns(df):
    return [c for c in df.columns if c not in DROP_GBM]

# Pengaturan terpilih dari Step 9
DEFAULT_PARAMS = dict(
    n_estimators=300,
    learning_rate=0.03,
    num_leaves=4,
    min_child_samples=40,
    subsample=0.8,
    subsample_freq=1,
    colsample_bytree=0.8,
    reg_lambda=5.0,
    random_state=42,
    verbosity=-1,
)

def make_fit_predict_gbm(drop=(), **overrides):
    params = {**DEFAULT_PARAMS, **overrides}
    def fit_predict(tr, va):
        cols = [c for c in gbm_columns(tr) if c not in drop]
        model = lgb.LGBMClassifier(**params)
        model.fit(tr[cols], tr[TARGET])
        return model.predict_proba(va[cols])[:, 1]
    return fit_predict