
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT_DIR))

from backend.app.ml.message_model import predict_message

test_messages = [
    "Hey, are we meeting for lunch tomorrow?",
    "Congratulations! You have won a free prize. Call now to claim your reward!",
    "URGENT! Your account has been suspended. Verify your details immediately.",
    "I'll reach home in 10 minutes.",
    "You have been selected for a cash prize. Reply WIN to claim."
]

for message in test_messages:
    print("\nMessage:", message)

    try:
        result = predict_message(message)

        print("Prediction:", result["prediction"])
        print("Spam probability:", result["spam_probability"])
        print("Risk score:", result["risk_score"])
        print("Model:", result["model"])

    except Exception as error:
        print("Error:", error)
