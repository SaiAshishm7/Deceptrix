
import sys
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.feature_extraction.url_features import extract_url_features

test_urls = [
    "https://www.google.com/",
    "http://example.com/login",
    "https://secure-bank-login.example.com/verify?id=123",
    "http://192.168.1.10/account",
]

for url in test_urls:
    print("\nURL:", url)
    features = extract_url_features(url)
    print(json.dumps(features, indent=4))
