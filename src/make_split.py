# src/make_split.py
from src.data import load, make_split
from src.features import TARGET

df = load()
dev, test = make_split(df)
dev.to_parquet("data/dev.parquet", index=False)
test.to_parquet("data/test.parquet", index=False)

print(f"dev : {len(dev)} baris, churn {dev[TARGET].mean():.3f}")
print(f"test: {len(test)} baris, churn {test[TARGET].mean():.3f}")
print(dev.groupby("fold")[TARGET].agg(["size", "mean"]).round(3))
print(dev["fold"].value_counts().sort_index())