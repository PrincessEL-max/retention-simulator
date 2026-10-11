# src/explain.py
import numpy as np
import pandas as pd
import lightgbm as lgb
import shap
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

from src.features import TARGET
from src.models_gbm import (get_categories, apply_categories, gbm_columns,
                            DEFAULT_PARAMS, BEST_PARAMS)

OUT = Path("reports/figures")
OUT.mkdir(parents=True, exist_ok=True)

dev = pd.read_parquet("data/dev.parquet")
test = pd.read_parquet("data/test.parquet")
cats = get_categories(dev)
dev_g, test_g = apply_categories(dev, cats), apply_categories(test, cats)
cols = gbm_columns(dev_g)
assert "charge_vs_hist" not in cols and len(cols) == 22

# Model final = model yang sama dengan ujian akhir (dilatih di data belajar)
model = lgb.LGBMClassifier(**{**DEFAULT_PARAMS, **BEST_PARAMS})
model.fit(dev_g[cols], dev_g[TARGET])

# Jelaskan semua 7.043 pelanggan
X = pd.concat([dev_g[cols], test_g[cols]], ignore_index=True)
ids = pd.concat([dev["customer_id"], test["customer_id"]], ignore_index=True)

explainer = shap.TreeExplainer(model)
sv = explainer.shap_values(X)
if isinstance(sv, list):
    sv = sv[1]
sv = np.asarray(sv)
if sv.ndim == 3:
    sv = sv[:, :, 1]
base = float(np.ravel(explainer.expected_value)[-1])

# Cek: nilai dasar + jumlah poin harus sama dengan keluaran model
raw = model.predict(X, raw_score=True)
print("cek penjumlahan, selisih terbesar:", np.abs(base + sv.sum(axis=1) - raw).max())

# 1) Pengaruh rata-rata tiap fitur
imp = pd.Series(np.abs(sv).mean(axis=0), index=cols).sort_values(ascending=False)
print("\nPENGARUH RATA-RATA PER FITUR (makin besar makin berpengaruh)")
print(imp.round(3).to_string())
imp.to_csv("reports/shap_importance.csv", header=["rata_rata_abs_shap"])

# Grafik (kolom kategori diberi kode angka agar bisa digambar)
Xp = X.copy()
for c in cats:
    Xp[c] = Xp[c].cat.codes
plt.figure()
shap.summary_plot(sv, Xp, plot_type="bar", show=False)
plt.tight_layout(); plt.savefig(OUT / "shap_bar.png", dpi=150); plt.close()
plt.figure()
shap.summary_plot(sv, Xp, show=False)
plt.tight_layout(); plt.savefig(OUT / "shap_beeswarm.png", dpi=150); plt.close()

# 2) Efek per kategori (kontrak, metode bayar, jenis internet)
print("\nRATA-RATA POIN RISIKO PER KATEGORI")
for c in cats:
    j = cols.index(c)
    t = (pd.Series(sv[:, j]).groupby(X[c].astype(str).values)
           .agg(n="size", rata_poin="mean").round(2))
    print(f"\n{c}\n{t.to_string()}")

# 3) Penjelasan per pelanggan (teks)
def jelaskan(i, k=6):
    s = pd.Series(sv[i], index=cols)
    top = s.reindex(s.abs().sort_values(ascending=False).index)[:k]
    return pd.DataFrame({"nilai": X.iloc[i][top.index].astype(str).values,
                         "poin_risiko": top.round(2).values}, index=top.index)

p = 1 / (1 + np.exp(-raw))
for nama, i in [("risiko tertinggi", int(np.argmax(p))),
                ("risiko menengah", int(np.argmin(np.abs(p - 0.5))))]:
    print(f"\n{nama}: {ids[i]} (peluang model {p[i]:.2f})")
    print(jelaskan(i).to_string())

# 4) Simpan poin per pelanggan (untuk tab penjelasan di aplikasi)
shap_df = pd.DataFrame(sv, columns=["shap_" + c for c in cols])
shap_df.insert(0, "customer_id", ids.values)
shap_df.to_parquet("data/shap_values.parquet", index=False)
print("\ntersimpan: reports/figures/*.png, reports/shap_importance.csv, data/shap_values.parquet")