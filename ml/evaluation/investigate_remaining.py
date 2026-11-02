import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT_DIR))

import pandas as pd
from backend.app.feature_extraction.url_features import extract_url_features

df = pd.read_csv(ROOT_DIR / "ml/datasets/processed/comp_phish_cleaned.csv")

features = [
    "no_of_space",
    "count_com",
    "count_www"
]

count = 0

for _, row in df.iterrows():
    url = str(row["url"])
    extracted = extract_url_features(url)

    for feature in features:
        original = row[feature]
        actual = extracted[feature]

        if original != actual:
            print(f"\nURL: {url}")
            print(f"Feature: {feature}")
            print(f"Dataset: {original}")
            print(f"Extracted: {actual}")
            count += 1

            if count >= 50:
                break

    if count >= 50:
        break

print(f"\nFirst {count} mismatches displayed.")