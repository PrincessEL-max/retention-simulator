# src/features.py
ID_COL = "customer_id"
TARGET = "churned"

# Bukan input model: ID, target, dan band (membuang informasi dari kolom numeriknya)
EXCLUDE = [ID_COL, TARGET, "monthly_charge_band"]


# --- Daftar fitur untuk logistic regression ---
# Sengaja TIDAK dipakai (kembaran fitur lain): total_charges, avg_monthly_hist,
# n_addons, n_family, tenure_bucket, monthly_charge_band, is_month_to_month dll
# (info kontrak dan metode bayar sudah ada lewat kolom kategori)
NUM_LR = ["tenure_months", "monthly_charge",
          "n_protection", "n_streaming"]
BIN_LR = ["senior_citizen", "has_partner", "has_dependents",
          "paperless_billing", "phone_service", "multiple_lines"]
CAT_LR = ["contract", "payment_method", "internet_service"]

def add_interactions(df):
    """Fitur gabungan dari temuan EDA Minggu 1."""
    d = df.copy()
    d["mtm_x_echeck"]      = d["is_month_to_month"] * d["is_echeck"]
    d["mtm_x_fiber"]       = d["is_month_to_month"] * d["is_fiber"]
    d["mtm_fiber_echeck"]  = d["is_month_to_month"] * d["is_fiber"] * d["is_echeck"]
    d["mtm_x_tenure"]      = d["is_month_to_month"] * d["tenure_months"]
    return d