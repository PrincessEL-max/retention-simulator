# src/make_scored.py
import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score

from src.features import TARGET
from src.cv import cv_oof, report
from src.models_gbm import (get_categories, apply_categories,
                            make_fit_predict_gbm, DEFAULT_PARAMS)

KEEP = ["customer_id", TARGET, "monthly_charge", "tenure_months", "tenure_bucket",
        "contract", "monthly_charge_band", "internet_service", "payment_method",
        "n_protection", "n_streaming", "n_addons", "senior_citizen",
        "is_month_to_month", "is_fiber", "is_echeck"]

dev = pd.read_parquet("data/dev.parquet")
test = pd.read_parquet("data/test.parquet")
tp = pd.read_parquet("data/test_pred.parquet")[["customer_id", "p_gbm"]]

# 1) Pelanggan data belajar: skor dari model yang tidak pernah melihat mereka
cats = get_categories(dev)
dev_g = apply_categories(dev, cats)
oof = cv_oof(dev_g, make_fit_predict_gbm(**DEFAULT_PARAMS))
report(dev_g, oof, "Cek dev (harapan ~0.657 / lift 2.83 / brier 0.1348)")

a = dev[KEEP].copy()
a["p_churn"] = oof
a["split"] = "dev"

# 2) Pelanggan data ujian: skor yang tersimpan dari ujian akhir
b = test[KEEP].merge(tp, on="customer_id", how="left").rename(columns={"p_gbm": "p_churn"})
b["split"] = "test"
assert len(b) == len(test), "jumlah baris test berubah setelah digabung"

scored = pd.concat([a, b], ignore_index=True)

# 3) Pemeriksaan
assert len(scored) == 7043
assert scored["customer_id"].is_unique
assert scored["p_churn"].notna().all()
assert scored["p_churn"].between(0, 1).all()

y = scored[TARGET]
print("\nrata-rata prediksi", round(scored["p_churn"].mean(), 3),
      "| kenyataan", round(y.mean(), 3))
for s, g in scored.groupby("split"):
    print(f"{s:5s} n={len(g)}  PR-AUC {average_precision_score(g[TARGET], g['p_churn']):.3f}")
print("semua PR-AUC", round(average_precision_score(y, scored["p_churn"]), 3))

scored.to_parquet("data/scored.parquet", index=False)
print("tersimpan: data/scored.parquet", scored.shape)