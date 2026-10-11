"""Train and evaluate a baseline Telco churn classifier."""

import os
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import pandas_gbq
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
	average_precision_score,
	brier_score_loss,
	precision_score,
	recall_score,
	roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


PROJECT = os.environ.get("GCP_PROJECT_ID")
RANDOM_STATE = 42
TEST_SIZE = 0.2
THRESHOLD = 0.5
MODEL_PATH = Path(__file__).resolve().parents[1] / "models" / "churn_logistic.joblib"


def make_pipeline(numeric_features: list[str], categorical_features: list[str]) -> Pipeline:
	numeric_transformer = Pipeline(
		steps=[
			("imputer", SimpleImputer(strategy="median")),
			("scaler", StandardScaler()),
		]
	)
	categorical_transformer = Pipeline(
		steps=[
			("imputer", SimpleImputer(strategy="most_frequent")),
			("encoder", OneHotEncoder(handle_unknown="ignore")),
		]
	)
	preprocessor = ColumnTransformer(
		transformers=[
			("numeric", numeric_transformer, numeric_features),
			("categorical", categorical_transformer, categorical_features),
		]
	)
	return Pipeline(
		steps=[
			("preprocessor", preprocessor),
			("classifier", LogisticRegression(max_iter=1000, random_state=RANDOM_STATE)),
		]
	)


def main() -> None:
	if not PROJECT:
		raise RuntimeError("Set GCP_PROJECT_ID before running this script.")

	query = f"SELECT * FROM `{PROJECT}.telco.features`"
	data = pandas_gbq.read_gbq(query, project_id=PROJECT, dialect="standard")
	if data.empty:
		raise ValueError("The BigQuery features table is empty.")
	if "target_churn" not in data.columns:
		raise ValueError("The features table must contain target_churn.")

	target = data.pop("target_churn").astype("int8")
	predictors = data.drop(columns=["customerID", "Churn"], errors="ignore")
	if target.nunique() != 2:
		raise ValueError("Training requires both churn classes in target_churn.")

	numeric_features = predictors.select_dtypes(include=np.number).columns.tolist()
	categorical_features = predictors.select_dtypes(exclude=np.number).columns.tolist()
	if not numeric_features and not categorical_features:
		raise ValueError("No predictor columns found in the features table.")

	x_train, x_test, y_train, y_test = train_test_split(
		predictors,
		target,
		test_size=TEST_SIZE,
		random_state=RANDOM_STATE,
		stratify=target,
	)

	evaluation_model = make_pipeline(numeric_features, categorical_features)
	evaluation_model.fit(x_train, y_train)
	probabilities = evaluation_model.predict_proba(x_test)[:, 1]
	predictions = (probabilities >= THRESHOLD).astype("int8")
	metrics = {
		"average_precision": average_precision_score(y_test, probabilities),
		"roc_auc": roc_auc_score(y_test, probabilities),
		"precision_at_0_5": precision_score(y_test, predictions, zero_division=0),
		"recall_at_0_5": recall_score(y_test, predictions, zero_division=0),
		"brier_score": brier_score_loss(y_test, probabilities),
	}

	final_model = make_pipeline(numeric_features, categorical_features)
	final_model.fit(predictors, target)
	MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
	joblib.dump(
		{
			"model": final_model,
			"feature_columns": predictors.columns.tolist(),
			"threshold": THRESHOLD,
			"metrics": metrics,
		},
		MODEL_PATH,
	)

	print(f"Rows: {len(data)} | churn rate: {target.mean():.1%}")
	for name, value in metrics.items():
		print(f"{name}: {value:.4f}")
	print(f"Model saved to {MODEL_PATH}")


if __name__ == "__main__":
	main()
