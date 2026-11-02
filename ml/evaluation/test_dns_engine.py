
import sys
from pathlib import Path
import json

ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT_DIR))

from backend.app.engines.dns_engine import analyze_dns

test_urls = [
    "https://www.google.com",
    "https://github.com",
    "https://example.com",
    "http://192.168.1.10/login"
]

for url in test_urls:
    print("\n" + "=" * 60)
    print("URL:", url)

    try:
        result = analyze_dns(url)
        print(json.dumps(result, indent=4))

    except Exception as error:
        print("ERROR:", str(error))
