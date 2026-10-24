import pandas as pd
import numpy as np
from sklearn.metrics import roc_auc_score

# Load dataset
df = pd.read_csv("data/HCV-Egy-Data.csv")

# Clean column names
df.columns = df.columns.str.strip()

# Convert required columns
cols = [
    "Age",
    "AST 1",
    "ALT 1",
    "Plat",
    "Baselinehistological staging"
]

for col in cols:
    df[col] = pd.to_numeric(df[col], errors="coerce")

df = df.dropna(subset=cols).copy()

# Calculate FIB-4
df["FIB4"] = (
    df["Age"] * df["AST 1"]
) / (
    df["Plat"] * np.sqrt(df["ALT 1"])
)

# Remove invalid values
df = df.replace([np.inf, -np.inf], np.nan)
df = df.dropna(subset=["FIB4"])

# Binary target
df["advanced_fibrosis"] = (
    df["Baselinehistological staging"] >= 3
).astype(int)

print("\n==============================")
print("FIB-4 ANALYSIS")
print("==============================")

print("\nFIB-4 statistics:")
print(df["FIB4"].describe())

print("\nFIB-4 by fibrosis stage:")
print(
    df.groupby("Baselinehistological staging")["FIB4"]
    .agg(["count", "mean", "median", "min", "max"])
)

# ROC-AUC
auc = roc_auc_score(
    df["advanced_fibrosis"],
    df["FIB4"]
)

print("\nFIB-4 ROC-AUC:", round(auc, 4))

print("\nStage distribution:")
print(
    df["Baselinehistological staging"].value_counts().sort_index()
)

print("\nAdvanced fibrosis distribution:")
print(
    df["advanced_fibrosis"].value_counts()
)