
from pathlib import Path

import joblib

ROOT_DIR = Path(__file__).resolve().parents[3]

MODEL_PATH = (
    ROOT_DIR / "ml/saved_models/message/logistic_regression.joblib"
)

model = joblib.load(MODEL_PATH)


def predict_message(message: str):
    if not isinstance(message, str) or not message.strip():
        raise ValueError("A valid message is required")

    message = message.strip()

    probabilities = model.predict_proba([message])[0]

    spam_index = list(model.classes_).index(1)
    spam_probability = float(probabilities[spam_index])

    prediction = int(spam_probability >= 0.5)

    return {
        "prediction": "spam" if prediction else "legitimate",
        "spam_probability": round(spam_probability, 4),
        "risk_score": round(spam_probability * 100, 2),
        "model": "Logistic Regression",
        "classification": "Spam detection"
    }
