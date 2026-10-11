# src/final_eval.py
# UJIAN AKHIR: hanya boleh dijalankan SATU KALI.
import json, sys, datetime
from pathlib import Path
import numpy as np, pandas as pd
from sklearn.metrics import average_precision_score, brier_score_loss

from src.features import TARGET, NUM_LR, BIN_LR, CAT_LR
from src.metrics import summary, lift_at, reliability, gain_table
from src.models_seg import segment_baseline
from src.models_lr import make_fit_predict
from src.models_gbm import (get_categories, apply_categories, gbm_columns,
                            make_fit_predict_gbm, DEFAULT_PARAMS)

SEAL = Path("reports/test_results.json")
if SEAL.exists():
    sys.exit("SEGEL TERBUKA: ujian akhir sudah pernah dijalankan. Jangan diulang.")

dev = pd.read_parquet("data/dev.parquet")
test = pd.read_parquet("data/test.parquet")

# --- Pemeriksaan keamanan ---
assert set(dev["customer_id"]).isdisjoint(set(test["customer_id"])), "ID dev dan test tumpang tindih!"
assert "charge_vs_hist" not in NUM_LR, "charge_vs_hist masih ada di NUM_LR"

cats = get_categories(dev)
dev_g, test_g = apply_categories(dev, cats), apply_categories(test, cats)
assert "charge_vs_hist" not in gbm_columns(dev_g), "charge_vs_hist masih dipakai LightGBM"
assert test_g[list(cats)].isna().sum().sum() == 0, "ada kategori kosong di test"
assert set(gbm_columns(test_g)) == set(gbm_columns(dev_g)), "kolom dev dan test berbeda"

# --- Latih di dev, prediksi test ---
y = test[TARGET].values
p_gbm = make_fit_predict_gbm(**DEFAULT_PARAMS)(dev_g, test_g)
numB = NUM_LR + ["mtm_x_tenure"]
binB = BIN_LR + ["mtm_x_echeck", "mtm_x_fiber", "mtm_fiber_echeck"]
p_lr = make_fit_predict(numB, binB, CAT_LR, C=0.3, interactions=True)(dev, test)
p_seg = segment_baseline(dev, test)
preds = {"Tebakan segmen": p_seg, "Logistik B": p_lr, "LightGBM": p_gbm}

# --- Rentang goyangan: acak ulang pelanggan ujian 1000 kali ---
rng = np.random.default_rng(42)
boot = {k: {"pr_auc": [], "lift10": [], "brier": []} for k in preds}
for _ in range(1000):
    i = rng.integers(0, len(y), len(y))
    if y[i].sum() == 0:
        continue
    for k, p in preds.items():
        boot[k]["pr_auc"].append(average_precision_score(y[i], p[i]))
        boot[k]["lift10"].append(lift_at(y[i], p[i], 0.10))
        boot[k]["brier"].append(brier_score_loss(y[i], p[i]))
boot = {k: {m: np.array(v) for m, v in d.items()} for k, d in boot.items()}
rentang = lambda a: [float(np.percentile(a, 2.5)), float(np.percentile(a, 97.5))]

# --- Simpan segel dan prediksi SEBELUM mencetak ---
result = {
    "dibuka_pada": datetime.datetime.now().isoformat(timespec="seconds"),
    "n_test": int(len(y)), "churn_rate_test": float(y.mean()),
    "params_lightgbm": DEFAULT_PARAMS, "C_logistik": 0.3,
    "metrik": {k: {m: float(v) for m, v in summary(y, p).items()} for k, p in preds.items()},
    "rentang_95": {k: {m: rentang(a) for m, a in d.items()} for k, d in boot.items()},
}
SEAL.parent.mkdir(exist_ok=True)
SEAL.write_text(json.dumps(result, indent=2))
pd.DataFrame({"customer_id": test["customer_id"], TARGET: y, "p_gbm": p_gbm,
              "p_lr": p_lr, "p_seg": p_seg}).to_parquet("data/test_pred.parquet", index=False)

# --- Cetak ---
print(f"\nUJIAN AKHIR: {len(y)} pelanggan, churn {y.mean():.3f}\n")
for k, p in preds.items():
    s, r = result["metrik"][k], result["rentang_95"][k]
    print(f"{k:15s} PR-AUC {s['pr_auc']:.3f} [{r['pr_auc'][0]:.3f}-{r['pr_auc'][1]:.3f}] | "
          f"lift@10% {s['lift@10%']:.2f} [{r['lift10'][0]:.2f}-{r['lift10'][1]:.2f}] | "
          f"brier {s['brier']:.4f} [{r['brier'][0]:.4f}-{r['brier'][1]:.4f}]")

print("\nSELISIH (positif = model pertama lebih baik)")
for a, b in [("LightGBM", "Tebakan segmen"), ("Logistik B", "Tebakan segmen"), ("LightGBM", "Logistik B")]:
    d_ap = boot[a]["pr_auc"] - boot[b]["pr_auc"]
    d_br = boot[b]["brier"] - boot[a]["brier"]
    print(f"{a} vs {b}: ketepatan urutan {d_ap.mean():+.3f} {np.round(rentang(d_ap), 3)} "
          f"(lebih baik di {(d_ap > 0).mean():.0%} acakan) | kejujuran {d_br.mean():+.4f}")

print("\nDAFTAR TERATAS (LightGBM)"); print(gain_table(y, p_gbm).to_string(index=False))
print("\nPELUANG vs KENYATAAN (LightGBM)"); print(reliability(y, p_gbm))
print(f"\nSemua -> prediksi {p_gbm.mean():.3f} | kenyataan {y.mean():.3f}")