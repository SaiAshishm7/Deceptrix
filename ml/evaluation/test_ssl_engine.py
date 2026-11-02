
import sys
from pathlib import Path
import json

ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT_DIR))

from backend.app.engines.ssl_engine import analyze_ssl

test_urls = [
    "https://www.google.com",
    "https://github.com",
    "http://example.com",
    "https://192.168.1.10",
]

for url in test_urls:
    print("\n" + "=" * 65)
    print("URL:", url)

    try:
        result = analyze_ssl(url)
        print(json.dumps(result, indent=4))

    except Exception as error:
        print("ERROR:", str(error))
