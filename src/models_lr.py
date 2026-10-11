# src/models_lr.py
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.linear_model import LogisticRegression
from src.features import TARGET, add_interactions

def build_lr(num, binary, cat, C=1.0):
    pre = ColumnTransformer([
        ("num", StandardScaler(), num),                       # samakan skala angka
        ("bin", "passthrough", binary),                       # ya/tidak: apa adanya
        ("cat", OneHotEncoder(handle_unknown="ignore"), cat), # kategori -> kolom 0/1
    ])
    return Pipeline([("pre", pre),
                     ("lr", LogisticRegression(C=C, max_iter=2000))])

def make_fit_predict(num, binary, cat, C=1.0, interactions=False):
    cols = num + binary + cat
    def fit_predict(tr, va):
        if interactions:
            tr, va = add_interactions(tr), add_interactions(va)
        model = build_lr(num, binary, cat, C)
        model.fit(tr[cols], tr[TARGET])
        return model.predict_proba(va[cols])[:, 1]
    return fit_predict