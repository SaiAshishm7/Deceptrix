
import json
from pathlib import Path

import numpy as np
import pandas as pd
import tldextract

from sklearn.model_selection import StratifiedGroupKFold

ROOT_DIR = Path(__file__).resolve().parents[2]

INPUT_FILE = ROOT_DIR / "ml/datasets/processed/comp_phish_cleaned.csv"
OUTPUT_DIR = ROOT_DIR / "ml/datasets/processed"

FEATURE_COLUMNS = [
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
    "shortest_word_length"
]

extract_domain = tldextract.TLDExtract(
    suffix_list_urls=(),
    include_psl_private_domains=True
)

def get_domain(url):
    extracted = extract_domain(str(url))
    domain = extracted.top_domain_under_public_suffix

    if domain:
        return domain.lower()

    return str(url).lower()


def main():
    df = pd.read_csv(INPUT_FILE)

    required_columns = ["url", "label"] + FEATURE_COLUMNS
    missing = [col for col in required_columns if col not in df.columns]

    if missing:
        raise ValueError(f"Missing columns: {missing}")

    df = df[required_columns].copy()

    df["label"] = pd.to_numeric(df["label"], errors="raise").astype(int)

    if not set(df["label"].unique()).issubset({0, 1}):
        raise ValueError("Labels must be 0 or 1")

    df[FEATURE_COLUMNS] = df[FEATURE_COLUMNS].apply(
        pd.to_numeric, errors="raise"
    )

    if df[FEATURE_COLUMNS].isnull().any().any():
        raise ValueError("Feature matrix contains missing values")

    if not np.isfinite(df[FEATURE_COLUMNS].to_numpy()).all():
        raise ValueError("Feature matrix contains non-finite values")

    df["domain_group"] = df["url"].apply(get_domain)

    X = df[FEATURE_COLUMNS]
    y = df["label"]
    groups = df["domain_group"]

    splitter = StratifiedGroupKFold(
        n_splits=5,
        shuffle=True,
        random_state=42
    )

    best_split = None
    best_difference = float("inf")
    overall_ratio = y.mean()

    for train_idx, test_idx in splitter.split(X, y, groups):
        test_ratio = y.iloc[test_idx].mean()
        difference = abs(test_ratio - overall_ratio)

        if difference < best_difference:
            best_difference = difference
            best_split = (train_idx, test_idx)

    train_idx, test_idx = best_split

    train_df = df.iloc[train_idx].copy()
    test_df = df.iloc[test_idx].copy()

    train_domains = set(train_df["domain_group"])
    test_domains = set(test_df["domain_group"])

    if train_domains.intersection(test_domains):
        raise RuntimeError("Domain leakage detected")

    train_df.drop(columns=["domain_group"]).to_csv(
        OUTPUT_DIR / "url_train.csv", index=False
    )

    test_df.drop(columns=["domain_group"]).to_csv(
        OUTPUT_DIR / "url_test.csv", index=False
    )

    with open(OUTPUT_DIR / "url_feature_columns.json", "w") as file:
        json.dump(FEATURE_COLUMNS, file, indent=4)

    print("\n========== FEATURE MATRIX SUMMARY ==========")
    print("Total records:", len(df))
    print("Total features:", len(FEATURE_COLUMNS))
    print("Unique domain groups:", groups.nunique())

    print("\nTraining records:", len(train_df))
    print("Testing records:", len(test_df))

    print("\nTraining label distribution:")
    print(train_df["label"].value_counts().sort_index())

    print("\nTesting label distribution:")
    print(test_df["label"].value_counts().sort_index())

    print("\nTraining phishing ratio:", round(train_df["label"].mean(), 4))
    print("Testing phishing ratio:", round(test_df["label"].mean(), 4))

    print("\nShared domains:", len(train_domains.intersection(test_domains)))

    print("\nSaved:")
    print("ml/datasets/processed/url_train.csv")
    print("ml/datasets/processed/url_test.csv")
    print("ml/datasets/processed/url_feature_columns.json")


if __name__ == "__main__":
    main()
