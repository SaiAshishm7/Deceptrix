
import pandas as pd
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]

DATASET_DIR = ROOT_DIR / "ml/datasets/raw/message"
OUTPUT_DIR = ROOT_DIR / "ml/datasets/processed/message"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

dataset_file = DATASET_DIR / "SMSSpamCollection"

df = pd.read_csv(
    dataset_file,
    sep="\t",
    header=None,
    names=["label", "message"],
    encoding="utf-8"
)

df["label"] = df["label"].map({
    "ham": 0,
    "spam": 1
})

df = df.dropna(subset=["label", "message"])
df["label"] = df["label"].astype(int)
df["message"] = df["message"].astype(str).str.strip()

df = df[df["message"] != ""]
df = df.drop_duplicates(subset=["message"])

output_file = OUTPUT_DIR / "sms_messages.csv"
df.to_csv(output_file, index=False)

print("========== MESSAGE DATASET SUMMARY ==========")
print("Total messages:", len(df))
print("\nLabel distribution:")
print(df["label"].value_counts().sort_index())
print("\nMissing values:")
print(df.isnull().sum())
print("\nSample messages:")
print(df.sample(min(5, len(df)), random_state=42).to_string(index=False))
print("\nSaved:", output_file)
