
import json
from pathlib import Path

import joblib
import pandas as pd

from backend.app.feature_extraction.url_features import extract_url_features

ROOT_DIR = Path(__file__).resolve().parents[3]

MODEL_PATH = ROOT_DIR / "ml/saved_models/random_forest_url_model.joblib"
FEATURE_PATH = ROOT_DIR / "ml/datasets/processed/url_feature_columns.json"

with open(FEATURE_PATH) as file:
    FEATURE_COLUMNS = json.load(file)

model = joblib.load(MODEL_PATH)


def predict_url(url: str):
    if not isinstance(url, str) or not url.strip():
        raise ValueError("A valid URL is required")

    features = extract_url_features(url.strip())

    missing = [
        feature for feature in FEATURE_COLUMNS
        if feature not in features
    ]

    if missing:
        raise ValueError(f"Missing extracted features: {missing}")

    input_data = pd.DataFrame(
        [[features[feature] for feature in FEATURE_COLUMNS]],
        columns=FEATURE_COLUMNS
    )

    probability = float(model.predict_proba(input_data)[0][1])
    prediction = int(probability >= 0.5)

    return {
        "prediction": "phishing" if prediction == 1 else "legitimate",
        "phishing_probability": round(probability, 4),
        "risk_score": round(probability * 100, 2),
        "model": "Random Forest",
        "features_used": len(FEATURE_COLUMNS)
    }
