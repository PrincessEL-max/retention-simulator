import pandas as pd
from sklearn.metrics import roc_auc_score

df = pd.read_parquet("data/features.parquet")
y = df["churned"]
num = df.drop(columns=["churned"]).select_dtypes("number")

auc = {}
for c in num.columns:
    a = roc_auc_score(y, num[c])
    auc[c] = max(a, 1 - a)          # arah tidak penting, yang dicari kekuatannya

print(pd.Series(auc).sort_values(ascending=False).round(3))