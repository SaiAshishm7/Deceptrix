
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.feature_extraction.url_features import extract_url_features

DATA_PATH = PROJECT_ROOT / "ml/datasets/processed/comp_phish_cleaned.csv"

df = pd.read_csv(DATA_PATH)

test_features = [
    "dots_path",
    "url_length",
    "domain_length",
    "url_contains_ip",
    "special_characters_count",
    "no_of_at",
    "no_of_comma",
    "no_of_dollar",
    "no_of_semicolon",
    "no_of_space",
    "no_of_ampersand",
    "no_of_dots",
    "no_of_equal",
    "no_of_percent",
    "no_of_underscore",
    "no_of_hyphen",
    "no_of_questionmark",
    "no_of_colon",
    "no_of_slashes_inpath",
    "has_asterisk",
    "has_or",
    "has_embedded_url",
    "uses_https",
    "num_query_params",
    "numeric_proportion",
    "url_entropy",
    "hostname_digit_ratio",
    "has_redirections",
    "has_punycode",
    "count_www",
    "count_com",
    "url_has_high_risk_extension",
    "has_explicit_port",
    "total_words_url",
    "average_length_of_words",
    "longest_word_length",
    "shortest_word_length",
]

mismatch_count = 0
total_comparisons = 0

for _, row in df.iterrows():
    url = row["url"]

    extracted = extract_url_features(url)

    for feature in test_features:
        original = row[feature]
        calculated = extracted[feature]

        matches = abs(float(original) - float(calculated)) < 1e-9

        total_comparisons += 1

        if not matches:
            mismatch_count += 1

            if mismatch_count <= 30:
                print(
                    f"{url} | {feature} | "
                    f"Dataset={original} | Extracted={calculated}"
                )

print("\n========== VALIDATION SUMMARY ==========")
print("Total URLs:", len(df))
print("Total feature comparisons:", total_comparisons)
print("Mismatches:", mismatch_count)

if total_comparisons > 0:
    print(
        "Match percentage:",
        round(
            (total_comparisons - mismatch_count)
            / total_comparisons * 100,
            2
        ),
        "%"
    )
else:
    print("Match percentage: N/A (no comparisons)")
