# src/data.py
import pandas as pd
from sklearn.model_selection import train_test_split, StratifiedKFold
from src.features import TARGET

SEED = 42

def load():
    return pd.read_parquet("data/features.parquet")

def make_split(df, n_folds=5):
    """Kunci 20% sebagai test; sisanya (dev) diberi nomor lipatan 0..4."""
    dev, test = train_test_split(
        df, test_size=0.2, stratify=df[TARGET], random_state=SEED
    )
    dev = dev.reset_index(drop=True)
    test = test.reset_index(drop=True)

    dev["fold"] = -1
    skf = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=SEED)
    for k, (_, va_idx) in enumerate(skf.split(dev, dev[TARGET])):
        dev.loc[va_idx, "fold"] = k
    return dev, test