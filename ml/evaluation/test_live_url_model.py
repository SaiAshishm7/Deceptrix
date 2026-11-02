
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT_DIR))

from backend.app.ml.url_model import predict_url

test_urls = [
    "https://www.google.com",
    "http://paypal-secure-login.example.com/account/verify",
    "https://github.com",
    "http://192.168.1.10/login"
]

for url in test_urls:
    print("\nURL:", url)

    try:
        result = predict_url(url)
        print("Prediction:", result["prediction"])
        print("Phishing probability:", result["phishing_probability"])
        print("Risk score:", result["risk_score"])
        print("Model:", result["model"])
    except Exception as error:
        print("Error:", error)
