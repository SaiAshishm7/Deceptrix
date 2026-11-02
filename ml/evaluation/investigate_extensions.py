import pandas as pd

path = "ml/datasets/processed/comp_phish_cleaned.csv"
df = pd.read_csv(path)

extensions = [
    ".exe", ".msi", ".bat", ".cmd", ".vbs", ".ps1",
    ".jar", ".scr", ".app", ".dmg", ".pkg", ".sh",
    ".run", ".bin", ".py", ".air", ".apk", ".elf",
    ".zip", ".rar", ".7z"
]

mismatches = df[
    df["url_has_high_risk_extension"] !=
    df["url"].apply(
        lambda url: int(
            any(ext in url.lower() for ext in extensions)
        )
    )
]

print("Mismatches using substring matching:", len(mismatches))

print("\nFirst 30 mismatches:")
print(
    mismatches[
        ["url", "url_has_high_risk_extension"]
    ].head(30).to_string(index=False)
)

print("\nExamples marked risky by dataset:")
print(
    df[df["url_has_high_risk_extension"] == 1][
        ["url", "label"]
    ].head(30).to_string(index=False)
)
