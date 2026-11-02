
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    classification_report
)

ROOT_DIR = Path(__file__).resolve().parents[2]

DATA_DIR = ROOT_DIR / "ml/datasets/processed"
MODEL_DIR = ROOT_DIR / "ml/saved_models"
TUNED_DIR = MODEL_DIR / "tuned_candidates"

REPORT_DIR = ROOT_DIR / "ml/evaluation/results/url_final_evaluation"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

test_df = pd.read_csv(DATA_DIR / "url_test.csv")

with open(DATA_DIR / "url_feature_columns.json") as file:
    feature_columns = json.load(file)

X_test = test_df[feature_columns]
y_test = test_df["label"]

if X_test.isnull().any().any():
    raise ValueError("Missing test features detected")

if not np.isfinite(X_test.to_numpy()).all():
    raise ValueError("Non-finite test features detected")

models = {
    "Original Random Forest": MODEL_DIR / "random_forest_url_model.joblib",
    "Original XGBoost": MODEL_DIR / "xgboost_url_model.joblib",
    "Tuned Random Forest": TUNED_DIR / "random_forest_tuned_candidate.joblib",
    "Tuned XGBoost": TUNED_DIR / "xgboost_tuned_candidate.joblib"
}

results = {}
error_records = []

print("\n========== FINAL URL MODEL EVALUATION ==========")
print("Held-out test records:", len(test_df))
print("Test set is not used for training or tuning.")

for name, model_path in models.items():
    if not model_path.exists():
        raise FileNotFoundError(f"Model not found: {model_path}")

    model = joblib.load(model_path)

    predictions = model.predict(X_test)
    probabilities = model.predict_proba(X_test)[:, 1]

    metrics = {
        "accuracy": float(accuracy_score(y_test, predictions)),
        "precision": float(
            precision_score(y_test, predictions, zero_division=0)
        ),
        "recall": float(
            recall_score(y_test, predictions, zero_division=0)
        ),
        "f1_score": float(
            f1_score(y_test, predictions, zero_division=0)
        ),
        "roc_auc": float(roc_auc_score(y_test, probabilities))
    }

    matrix = confusion_matrix(y_test, predictions, labels=[0, 1])

    results[name] = {
        "metrics": metrics,
        "confusion_matrix": matrix.tolist()
    }

    print(f"\n========== {name.upper()} ==========")

    for metric, value in metrics.items():
        print(f"{metric}: {value:.4f}")

    print("\nClassification Report:")
    print(
        classification_report(
            y_test,
            predictions,
            target_names=["Legitimate", "Phishing"],
            zero_division=0
        )
    )

    print("Confusion Matrix:")
    print(matrix)

    for index, prediction in enumerate(predictions):
        actual = int(y_test.iloc[index])

        if actual != int(prediction):
            error_records.append({
                "model": name,
                "url": test_df.iloc[index]["url"],
                "actual": actual,
                "predicted": int(prediction),
                "phishing_probability": float(probabilities[index])
            })

with open(REPORT_DIR / "final_model_comparison.json", "w") as file:
    json.dump(results, file, indent=4)

comparison = pd.DataFrame({
    name: data["metrics"]
    for name, data in results.items()
}).T

comparison.to_csv(REPORT_DIR / "final_model_comparison.csv")

pd.DataFrame(error_records).to_csv(
    REPORT_DIR / "misclassified_urls.csv",
    index=False
)

print("\n========== FINAL MODEL COMPARISON ==========")
print(comparison.to_string())

print("\nSaved evaluation reports to:")
print(REPORT_DIR)
