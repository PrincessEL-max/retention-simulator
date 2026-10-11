# src/models_seg.py
import numpy as np
from src.features import TARGET

def segment_baseline(tr, va):
    rata2 = tr[TARGET].mean()
    g = tr.groupby(["tenure_bucket", "contract"])[TARGET].mean()
    return np.array([g.get(k, rata2) for k in zip(va["tenure_bucket"], va["contract"])])