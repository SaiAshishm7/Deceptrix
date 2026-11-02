
import pandas as pd
from pathlib import Path

path = Path("ml/datasets/raw/Data_Dictionary.xlsx")

df = pd.read_excel(path)

df = df.dropna(subset=["Feature Name"])

for _, row in df.iterrows():
    print("\n" + "=" * 70)
    print("FEATURE:", row["Feature Name"])
    print("CATEGORY:", row["Category"])
    print("DATA TYPE:", row["Data Type"])
    print("DESCRIPTION:", row["Description"])
    print("COMPUTATION RULE:", row["Computational Rule/Threshold/Criteria"])
