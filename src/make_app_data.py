# src/make_app_data.py
import pandas as pd

sc = pd.read_parquet("data/scored.parquet")
sh = pd.read_parquet("data/shap_values.parquet")
m = sc.merge(sh, on="customer_id", how="left", validate="one_to_one")
shap_cols = [c for c in m.columns if c.startswith("shap_")]
assert len(m) == 7043 and len(shap_cols) == 22 and m[shap_cols].notna().all().all()

kolom = ["p_churn", "churned", "monthly_charge", "tenure_bucket", "contract",
         "monthly_charge_band", "internet_service", "payment_method",
         "n_protection", "senior_citizen", "split"] + shap_cols
app = m[kolom].sample(frac=1, random_state=42).reset_index(drop=True)
app.insert(0, "id", ["P" + str(i + 1).zfill(4) for i in range(len(app))])
app.to_parquet("app/app_data.parquet", index=False)
print(app.shape)   # harapan: (7043, 34)