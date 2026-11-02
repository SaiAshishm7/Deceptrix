
import pandas as pd
from pathlib import Path

RAW_PATH = Path("ml/datasets/raw/All_Features_threshold90.xlsx")
OUTPUT_PATH = Path("ml/datasets/processed/comp_phish_cleaned.csv")

def prepare_dataset():
    print("Loading CompPhish dataset...")

    df = pd.read_excel(RAW_PATH)

    print("Original records:", len(df))

    conflicting = df.groupby("url")["label"].nunique()
    conflicting = conflicting[conflicting > 1]

    if not conflicting.empty:
        raise ValueError(
            f"Found {len(conflicting)} URLs with conflicting labels."
        )

    df = df.drop_duplicates(subset=["url"], keep="first").copy()

    print("Records after duplicate removal:", len(df))
    print("Unique URLs:", df["url"].nunique())

    print("\nLabel distribution:")
    print(df["label"].value_counts())

    print("\nMissing values:", df.isnull().sum().sum())

    if not set(df["label"].unique()).issubset({0, 1}):
        raise ValueError("Unexpected label values found.")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False)

    print("\nCleaned dataset saved to:", OUTPUT_PATH)

if __name__ == "__main__":
    prepare_dataset()
