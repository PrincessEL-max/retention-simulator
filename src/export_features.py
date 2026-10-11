# src/export_features.py
import os
from google.cloud import bigquery

PROJECT = os.environ["GCP_PROJECT_ID"]
client = bigquery.Client(project=PROJECT)

df = client.query(f"SELECT * FROM `{PROJECT}.telco.features`").to_dataframe()
df.to_parquet("data/features.parquet", index=False)
print(df.shape)