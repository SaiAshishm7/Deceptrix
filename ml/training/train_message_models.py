
import json
from pathlib import Path

import joblib
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    classification_report,
    confusion_matrix
)

ROOT_DIR = Path(__file__).resolve().parents[2]

DATA_FILE = ROOT_DIR / "ml/datasets/processed/message/sms_messages.csv"
MODEL_DIR = ROOT_DIR / "ml/saved_models/message"
RESULT_DIR = ROOT_DIR / "ml/evaluation/results/message"

MODEL_DIR.mkdir(parents=True, exist_ok=True)
RESULT_DIR.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(DATA_FILE)

X = df["message"].astype(str)
y = df["label"].astype(int)

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)

models = {
    "Logistic Regression": Pipeline([
        ("tfidf", TfidfVectorizer(
            lowercase=True,
            stop_words=None,
            ngram_range=(1, 2),
            min_df=2,
            max_features=50000,
            sublinear_tf=True
        )),
        ("classifier", LogisticRegression(
            max_iter=1000,
            class_weight="balanced",
            random_state=42
        ))
    ]),

    "Multinomial Naive Bayes": Pipeline([
        ("tfidf", TfidfVectorizer(
            lowercase=True,
            stop_words=None,
            ngram_range=(1, 2),
            min_df=2,
            max_features=50000
        )),
        ("classifier", MultinomialNB(alpha=0.5))
    ])
}

results = {}

print("========== MESSAGE DATASET ==========")
print("Total messages:", len(df))
print("Training messages:", len(X_train))
print("Testing messages:", len(X_test))
print("\nTraining labels:")
print(y_train.value_counts().sort_index())
print("\nTesting labels:")
print(y_test.value_counts().sort_index())

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

    print("\nClassification report:")
    print(classification_report(
        y_test,
        predictions,
        target_names=["Legitimate", "Spam"],
        zero_division=0
    ))

    print("Confusion matrix:")
    print(confusion_matrix(y_test, predictions))

    filename = name.lower().replace(" ", "_") + ".joblib"
    joblib.dump(model, MODEL_DIR / filename)

    print(f"\nSaved: ml/saved_models/message/{filename}")

with open(RESULT_DIR / "message_model_comparison.json", "w") as file:
    json.dump(results, file, indent=4)

print("\n========== MODEL COMPARISON ==========")
print(pd.DataFrame(results).T.to_string())

print("\nComparison saved successfully.")
