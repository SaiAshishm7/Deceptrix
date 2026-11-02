
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    classification_report,
    confusion_matrix
)

from xgboost import XGBClassifier

ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "ml/datasets/processed"
MODEL_DIR = ROOT_DIR / "ml/saved_models"
REPORT_DIR = ROOT_DIR / "ml/evaluation/results"

MODEL_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)

train_df = pd.read_csv(DATA_DIR / "url_train.csv")
test_df = pd.read_csv(DATA_DIR / "url_test.csv")

with open(DATA_DIR / "url_feature_columns.json") as file:
    FEATURE_COLUMNS = json.load(file)

X_train = train_df[FEATURE_COLUMNS]
y_train = train_df["label"]

X_test = test_df[FEATURE_COLUMNS]
y_test = test_df["label"]

if list(X_train.columns) != list(X_test.columns):
    raise ValueError("Training and testing feature order differs")

if X_train.isnull().any().any() or X_test.isnull().any().any():
    raise ValueError("Missing values detected")

if not np.isfinite(X_train.to_numpy()).all():
    raise ValueError("Non-finite training values detected")

if not np.isfinite(X_test.to_numpy()).all():
    raise ValueError("Non-finite testing values detected")

models = {
    "Random Forest": RandomForestClassifier(
        n_estimators=500,
        max_features="sqrt",
        min_samples_leaf=2,
        class_weight="balanced_subsample",
        random_state=42,
        n_jobs=-1
    ),
    "XGBoost": XGBClassifier(
        n_estimators=500,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        reg_lambda=1,
        objective="binary:logistic",
        eval_metric="logloss",
        random_state=42,
        n_jobs=-1
    )
}

results = {}

for name, model in models.items():
    print(f"\n========== TRAINING {name.upper()} ==========")

    model.fit(X_train, y_train)

    predictions = model.predict(X_test)
    probabilities = model.predict_proba(X_test)[:, 1]

    metrics = {
        "accuracy": float(accuracy_score(y_test, predictions)),
        "precision": float(precision_score(y_test, predictions, zero_division=0)),
        "recall": float(recall_score(y_test, predictions, zero_division=0)),
        "f1_score": float(f1_score(y_test, predictions, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_test, probabilities))
    }

    results[name] = metrics

    print("\nMetrics:")
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
    print(confusion_matrix(y_test, predictions))

    model_filename = name.lower().replace(" ", "_") + "_url_model.joblib"
    joblib.dump(model, MODEL_DIR / model_filename)

    importance = pd.DataFrame({
        "feature": FEATURE_COLUMNS,
        "importance": model.feature_importances_
    }).sort_values("importance", ascending=False)

    importance.to_csv(
        REPORT_DIR / f"{name.lower().replace(' ', '_')}_feature_importance.csv",
        index=False
    )

    print(f"\nSaved model: ml/saved_models/{model_filename}")

with open(REPORT_DIR / "url_model_comparison.json", "w") as file:
    json.dump(results, file, indent=4)

comparison = pd.DataFrame(results).T
comparison = comparison.sort_values("f1_score", ascending=False)

print("\n========== MODEL COMPARISON ==========")
print(comparison.to_string())

print("\nComparison saved to ml/evaluation/results/url_model_comparison.json")
print("\nBoth models trained and saved successfully.")
