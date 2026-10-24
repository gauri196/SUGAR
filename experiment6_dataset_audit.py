
from pathlib import Path
import json

import numpy as np
import pandas as pd

# --------------------------------------------------
# EXPERIMENT 6: DATASET QUALITY AND FEATURE AUDIT
# --------------------------------------------------

DATA_PATH = Path("data/HCV-Egy-Data.csv")
OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TARGET = "Baselinehistological staging"

BASELINE_FEATURES = [
    "Age", "BMI", "Plat", "AST 1", "ALT 1",
    "WBC", "RBC", "HGB",
]

# These variables are time-indexed or may be recorded
# after baseline. Inspect definitions before using them.
TIME_INDEXED_FEATURES = [
    col for col in [
        "ALT 4", "ALT 12", "ALT 24", "ALT 36", "ALT 48",
        "ALT after 24 w", "RNA Base", "RNA 4", "RNA 12",
        "RNA EOT", "RNA EF",
    ]
]

if not DATA_PATH.exists():
    raise FileNotFoundError(
        f"Could not find {DATA_PATH}. "
        "Run the script from your project root folder."
    )

df = pd.read_csv(DATA_PATH)
df.columns = df.columns.str.strip()

print("=" * 70)
print("EXPERIMENT 6: DATASET AUDIT")
print("=" * 70)

# --------------------------------------------------
# 1. BASIC DATASET INFORMATION
# --------------------------------------------------

print("\n1. DATASET OVERVIEW")
print("-" * 70)
print("Original shape:", df.shape)
print("Duplicate rows:", int(df.duplicated().sum()))
print("Column count:", len(df.columns))

print("\nAll column names:")
for i, col in enumerate(df.columns, start=1):
    print(f"{i:02d}. {col}")

print("\nData types:")
print(df.dtypes.astype(str).to_string())

# --------------------------------------------------
# 2. MISSING VALUES
# --------------------------------------------------

print("\n2. MISSING VALUES")
print("-" * 70)

missing = pd.DataFrame({
    "column": df.columns,
    "missing_count": df.isna().sum().values,
    "missing_percent": (
        df.isna().mean().values * 100
    ).round(2),
    "dtype": df.dtypes.astype(str).values,
})

missing = missing.sort_values(
    "missing_count", ascending=False
)

print(missing.to_string(index=False))

missing.to_csv(
    OUTPUT_DIR / "experiment6_missing_values.csv",
    index=False,
)

# --------------------------------------------------
# 3. UNIQUE VALUES AND POSSIBLE CATEGORICAL COLUMNS
# --------------------------------------------------

print("\n3. UNIQUE VALUES")
print("-" * 70)

unique_rows = []

for col in df.columns:
    non_missing = df[col].dropna()
    unique_count = non_missing.nunique()

    examples = non_missing.astype(str).unique()[:8]

    unique_rows.append({
        "column": col,
        "unique_non_missing": int(unique_count),
        "example_values": " | ".join(examples),
        "dtype": str(df[col].dtype),
    })

unique_df = pd.DataFrame(unique_rows)
print(unique_df.to_string(index=False))

unique_df.to_csv(
    OUTPUT_DIR / "experiment6_unique_values.csv",
    index=False,
)

# --------------------------------------------------
# 4. TARGET LABEL AUDIT
# --------------------------------------------------

print("\n4. TARGET LABELS")
print("-" * 70)

if TARGET not in df.columns:
    raise ValueError(f"Target column not found: {TARGET}")

target_numeric = pd.to_numeric(
    df[TARGET], errors="coerce"
)

print("Missing target labels:", int(target_numeric.isna().sum()))
print("\nTarget value counts, including missing:")
print(target_numeric.value_counts(dropna=False).sort_index())

valid = df.loc[
    target_numeric.isin([1, 2, 3, 4])
].copy()

valid[TARGET] = target_numeric.loc[valid.index].astype(int)

print("\nRows with stages 1, 2, 3, or 4:", len(valid))
print("\nStage distribution:")
print(valid[TARGET].value_counts().sort_index())

# --------------------------------------------------
# 5. NUMERIC FEATURE DISTRIBUTIONS
# --------------------------------------------------

print("\n5. NUMERIC DESCRIPTIVE STATISTICS")
print("-" * 70)

numeric = df.select_dtypes(include="number")

if not numeric.empty:
    descriptive = numeric.describe(
        percentiles=[0.01, 0.05, 0.25, 0.50, 0.75, 0.95, 0.99]
    ).T

    descriptive["missing_count"] = numeric.isna().sum()
    descriptive["zero_count"] = (numeric == 0).sum()
    descriptive["negative_count"] = (numeric < 0).sum()

    print(descriptive.round(3).to_string())

    descriptive.to_csv(
        OUTPUT_DIR / "experiment6_numeric_descriptive_stats.csv"
    )
else:
    print("No numeric columns found.")

# --------------------------------------------------
# 6. BASELINE FEATURES: QUALITY CHECK
# --------------------------------------------------

print("\n6. BASELINE FEATURE CHECK")
print("-" * 70)

available_baseline = [
    col for col in BASELINE_FEATURES
    if col in valid.columns
]

baseline_rows = []

for col in available_baseline:
    values = pd.to_numeric(valid[col], errors="coerce")
    finite = values[np.isfinite(values)]

    baseline_rows.append({
        "feature": col,
        "non_missing": int(values.notna().sum()),
        "missing": int(values.isna().sum()),
        "missing_percent": round(values.isna().mean() * 100, 2),
        "unique_values": int(values.nunique()),
        "min": finite.min() if len(finite) else np.nan,
        "p01": finite.quantile(0.01) if len(finite) else np.nan,
        "median": finite.median() if len(finite) else np.nan,
        "mean": finite.mean() if len(finite) else np.nan,
        "p99": finite.quantile(0.99) if len(finite) else np.nan,
        "max": finite.max() if len(finite) else np.nan,
        "zero_count": int((values == 0).sum()),
        "negative_count": int((values < 0).sum()),
    })

baseline_audit = pd.DataFrame(baseline_rows)
print(baseline_audit.round(3).to_string(index=False))

baseline_audit.to_csv(
    OUTPUT_DIR / "experiment6_baseline_feature_audit.csv",
    index=False,
)

# --------------------------------------------------
# 7. FEATURE DISTRIBUTIONS BY STAGE
# --------------------------------------------------

print("\n7. BASELINE FEATURES BY STAGE")
print("-" * 70)

if available_baseline:
    stage_summary = valid.groupby(TARGET)[
        available_baseline
    ].agg(["count", "mean", "median", "std"])

    print(stage_summary.round(3).to_string())

    stage_summary.to_csv(
        OUTPUT_DIR / "experiment6_features_by_stage.csv"
    )

# --------------------------------------------------
# 8. SPEARMAN CORRELATION WITH STAGE
# --------------------------------------------------

print("\n8. SPEARMAN CORRELATION WITH STAGE")
print("-" * 70)
print(
    "This is a simple exploratory check, not proof of "
    "predictive usefulness or causation."
)

correlation_features = [
    col for col in BASELINE_FEATURES
    if col in valid.columns
]

if correlation_features:
    corr_df = valid[
        correlation_features + [TARGET]
    ].apply(pd.to_numeric, errors="coerce")

    correlations = corr_df.corr(
        method="spearman"
    )[TARGET].drop(TARGET).sort_values()

    print(correlations.round(4).to_string())

    correlations.rename(
        "spearman_correlation_with_stage"
    ).to_csv(
        OUTPUT_DIR / "experiment6_stage_correlations.csv",
        header=True,
    )

# --------------------------------------------------
# 9. TIME-INDEXED FEATURE CHECK
# --------------------------------------------------

print("\n9. TIME-INDEXED / POTENTIALLY POST-BASELINE FIELDS")
print("-" * 70)

available_time_indexed = [
    col for col in TIME_INDEXED_FEATURES
    if col in df.columns
]

if available_time_indexed:
    for col in available_time_indexed:
        print(
            f"{col}: "
            f"{df[col].notna().sum()} non-missing values, "
            f"{df[col].nunique(dropna=True)} unique values"
        )
else:
    print("No matching time-indexed fields found.")
    print("Check the column list and official data dictionary.")

print(
    "\nReminder: a field name alone does not establish "
    "when it was measured. Verify its meaning in the "
    "dataset documentation before using it for baseline prediction."
)

# --------------------------------------------------
# 10. SAVE A SHORT AUDIT SUMMARY
# --------------------------------------------------

summary = {
    "original_rows": int(df.shape[0]),
    "original_columns": int(df.shape[1]),
    "duplicate_rows": int(df.duplicated().sum()),
    "missing_target_rows": int(target_numeric.isna().sum()),
    "valid_four_stage_rows": int(len(valid)),
    "stage_counts": {
        str(int(stage)): int(count)
        for stage, count in valid[TARGET].value_counts().sort_index().items()
    },
    "columns_with_missing_values": {
        str(row["column"]): {
            "count": int(row["missing_count"]),
            "percent": float(row["missing_percent"]),
        }
        for _, row in missing[missing["missing_count"] > 0].iterrows()
    },
    "baseline_features_checked": available_baseline,
    "time_indexed_fields_found": available_time_indexed,
}

summary_path = OUTPUT_DIR / "experiment6_audit_summary.json"

with open(summary_path, "w", encoding="utf-8") as file:
    json.dump(summary, file, indent=2)

print("\n" + "=" * 70)
print("AUDIT COMPLETED")
print("=" * 70)
print("Saved reports in:", OUTPUT_DIR)
print("1. experiment6_audit_summary.json")
print("2. experiment6_missing_values.csv")
print("3. experiment6_unique_values.csv")
print("4. experiment6_numeric_descriptive_stats.csv")
print("5. experiment6_baseline_feature_audit.csv")
print("6. experiment6_features_by_stage.csv")
print("7. experiment6_stage_correlations.csv")
