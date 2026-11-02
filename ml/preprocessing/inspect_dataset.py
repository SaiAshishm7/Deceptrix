
from pathlib import Path
import pandas as pd

DATA_DIR = Path("ml/datasets/raw")

FILES = [
    "All_Features_threshold90.xlsx",
    "Mapping_File.xlsx",
    "Data_Dictionary.xlsx"
]

def inspect_file(file_name):
    path = DATA_DIR / file_name

    print("\n" + "=" * 80)
    print(f"FILE: {file_name}")
    print("=" * 80)

    if not path.exists():
        print("File not found!")
        return

    excel = pd.ExcelFile(path)

    for sheet in excel.sheet_names:
        df = pd.read_excel(path, sheet_name=sheet)

        print(f"\nSHEET: {sheet}")
        print("-" * 60)
        print("Shape:", df.shape)

        print("\nColumns:")
        for col in df.columns:
            print(f"  {col} ({df[col].dtype})")

        print("\nMissing values:")
        missing = df.isnull().sum()
        print(missing[missing > 0] if missing.any() else "No missing values")

        print("\nDuplicate rows:", df.duplicated().sum())

        label_columns = [
            col for col in df.columns
            if any(word in str(col).lower()
                   for word in ["label", "class", "target"])
        ]

        for col in label_columns:
            print(f"\nLabel distribution: {col}")
            print(df[col].value_counts(dropna=False))

        url_columns = [
            col for col in df.columns
            if any(word in str(col).lower()
                   for word in ["url", "link", "domain"])
        ]

        print("\nPossible URL columns:", url_columns)

        print("\nFirst 5 rows:")
        print(df.head().to_string(max_cols=10))

def main():
    for file_name in FILES:
        inspect_file(file_name)

if __name__ == "__main__":
    main()
