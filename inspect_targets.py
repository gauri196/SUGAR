
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

# Dataset 1: HCV with baseline histological staging
hcv = pd.read_csv(DATA_DIR / "HCV-Egy-Data.csv")

hcv_target = "Baselinehistological staging"

print("\n=== HCV fibrosis-stage labels ===")
print("Total rows:", len(hcv))
print("Missing stage labels:", hcv[hcv_target].isna().sum())
print("\nStage distribution:")
print(hcv[hcv_target].value_counts(dropna=False).sort_index())

# Dataset 2: Mayo cirrhosis cohort
cirrhosis = pd.read_csv(DATA_DIR / "cirrhosis.csv")

print("\n=== Cirrhosis histological-stage labels ===")
print("Total rows:", len(cirrhosis))
print("Missing stage labels:", cirrhosis["Stage"].isna().sum())
print("\nStage distribution:")
print(cirrhosis["Stage"].value_counts(dropna=False).sort_index())

print("\n=== Candidate feature availability ===")

feature_groups = {
    "Routine": [
        "Age", "AST 1", "ALT 1", "Plat"
    ],
    "Liver-related": [
        "Albumin", "Bilirubin", "Alk_Phos",
        "SGOT", "Prothrombin"
    ],
    "Metabolic": [
        "BMI", "Cholesterol", "Tryglicerides",
        "Glucose", "HbA1c"
    ],
    "Etiology / disease context": [
        "Gender", "Drug", "Ascites",
        "Hepatomegaly", "Spiders"
    ],
}

for dataset_name, df in [
    ("HCV", hcv),
    ("Cirrhosis", cirrhosis),
]:
    print(f"\n{dataset_name}:")
    for group, columns in feature_groups.items():
        available = [c for c in columns if c in df.columns]
        print(f"  {group}: {available or 'No matching columns'}")
