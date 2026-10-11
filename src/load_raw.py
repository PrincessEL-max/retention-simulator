# src/load_raw.py
import os
import pandas as pd
from google.cloud import bigquery

PROJECT = os.environ["GCP_PROJECT_ID"]
TABLE = f"{PROJECT}.telco.raw"
CSV = "data/raw/WA_Fn-UseC_-Telco-Customer-Churn.csv"

# dtype=str + keep_default_na=False: tidak ada konversi tipe, tidak ada nilai yang "hilang" diam-diam
df = pd.read_csv(CSV, dtype=str, keep_default_na=False)

client = bigquery.Client(project=PROJECT)
job_config = bigquery.LoadJobConfig(
    schema=[bigquery.SchemaField(c, "STRING") for c in df.columns],
    write_disposition="WRITE_TRUNCATE",   # aman dijalankan ulang (idempoten)
)
client.load_table_from_dataframe(df, TABLE, job_config=job_config).result()

print(f"{client.get_table(TABLE).num_rows} baris dimuat ke {TABLE}")