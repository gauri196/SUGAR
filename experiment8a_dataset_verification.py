
from pathlib import Path
import pandas as pd
import numpy as np

DATA_PATH = Path("data/HCV-Egy-Data.csv")
OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)

TARGET = "Baselinehistological staging"
GRADE = "Baseline histological Grading"

BASELINE_FEATURES = [
    "Age", "BMI", "Plat", "AST 1", "ALT 1",
    "WBC", "RBC", "HGB",
]

EXPECTED_STAGES = [1, 2, 3, 4]


def section(title):
    print("\n" + "=" * 72)
    print(title)
    print("=" * 72)


def main():
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Could not find {DATA_PATH}. Run from the project root."
        )

    df = pd.read_csv(DATA_PATH)
    df.columns = df.columns.str.strip()

    section("1. DATASET STRUCTURE")
    print("File:", DATA_PATH)
    print("Rows:", len(df))
    print("Columns:", len(df.columns))
    print("Duplicate rows:", int(df.duplicated().sum()))
    print("\nColumn names:")
    for col in df.columns:
        print("-", repr(col))

    required = [TARGET, GRADE] + BASELINE_FEATURES
    missing_columns = [c for c in required if c not in df.columns]

    if missing_columns:
        print("\nERROR: Required columns not found:", missing_columns)
        return

    section("2. TARGET LABEL AUDIT")

    raw_target = df[TARGET]
    numeric_target = pd.to_numeric(raw_target, errors="coerce")

    print("Missing target labels:", int(raw_target.isna().sum()))
    print(
        "Non-numeric target values:",
        int((raw_target.notna() & numeric_target.isna()).sum())
    )
    print("\nRaw target values and counts:")
    print(raw_target.value_counts(dropna=False).sort_index().to_string())

    valid_target = numeric_target.isin(EXPECTED_STAGES)
    unexpected = numeric_target.notna() & ~valid_target

    print("\nUnexpected numeric target values:", int(unexpected.sum()))
    if unexpected.any():
        print(numeric_target[unexpected].value_counts().to_string())

    valid_df = df.loc[valid_target].copy()
    valid_df[TARGET] = numeric_target[valid_target].astype(int)

    print("\nRows with stages 1-4:", len(valid_df))
    print("Stage counts:")
    print(
        valid_df[TARGET]
        .value_counts()
        .reindex(EXPECTED_STAGES, fill_value=0)
        .sort_index()
        .to_string()
    )

    stage_counts = (
        valid_df[TARGET]
        .value_counts()
        .reindex(EXPECTED_STAGES, fill_value=0)
        .rename_axis("stage")
        .reset_index(name="count")
    )
    stage_counts["percentage"] = (
        stage_counts["count"] / len(valid_df) * 100
    )
    stage_counts.to_csv(
        OUTPUT_DIR / "experiment8a_stage_counts.csv", index=False
    )

    section("3. BASELINE FEATURE AUDIT")

    feature_rows = []

    for feature in BASELINE_FEATURES:
        original = df[feature]
        numeric = pd.to_numeric(original, errors="coerce")
        valid_values = numeric.dropna()

        row = {
            "feature": feature,
            "original_dtype": str(original.dtype),
            "missing_original": int(original.isna().sum()),
            "non_numeric_nonmissing": int(
                (original.notna() & numeric.isna()).sum()
            ),
            "unique_nonmissing": int(valid_values.nunique()),
            "minimum": valid_values.min() if len(valid_values) else np.nan,
            "median": valid_values.median() if len(valid_values) else np.nan,
            "maximum": valid_values.max() if len(valid_values) else np.nan,
            "zero_count": int((valid_values == 0).sum()),
            "negative_count": int((valid_values < 0).sum()),
        }
        feature_rows.append(row)

        print(
            f"\n{feature}: dtype={row['original_dtype']}, "
            f"missing={row['missing_original']}, "
            f"unique={row['unique_nonmissing']}"
        )
        print(
            f"  min={row['minimum']}, median={row['median']}, "
            f"max={row['maximum']}, zeros={row['zero_count']}, "
            f"negative={row['negative_count']}"
        )

    pd.DataFrame(feature_rows).to_csv(
        OUTPUT_DIR / "experiment8a_baseline_feature_audit.csv",
        index=False,
    )

    section("4. GENDER AND SYMPTOM CODING")

    categorical_features = [
        "Gender", "Fever", "Nausea/Vomting", "Headache",
        "Diarrhea", "Fatigue & generalized bone ache",
        "Jaundice", "Epigastric pain",
    ]

    category_rows = []

    for feature in categorical_features:
        if feature not in df.columns:
            continue

        counts = df[feature].value_counts(dropna=False)

        print(f"\n{feature}:")
        print(counts.to_string())

        for value, count in counts.items():
            category_rows.append({
                "feature": feature,
                "value": str(value),
                "count": int(count),
            })

    pd.DataFrame(category_rows).to_csv(
        OUTPUT_DIR / "experiment8a_category_counts.csv",
        index=False,
    )

    section("5. GRADING VS STAGING")

    grade_numeric = pd.to_numeric(df[GRADE], errors="coerce")
    grade_valid = grade_numeric.notna() & valid_target

    print("Grading missing values:", int(grade_numeric.isna().sum()))
    print("\nGrading values and counts:")
    print(grade_numeric.value_counts(dropna=False).sort_index().to_string())

    grade_stage = pd.DataFrame({
        "stage": numeric_target[grade_valid].astype(int),
        "grade": grade_numeric[grade_valid],
    })

    print("\nGrading distribution by stage:")
    print(
        grade_stage.groupby("stage")["grade"]
        .agg(["count", "min", "median", "mean", "max"])
        .round(3)
        .to_string()
    )

    print(
        "\nSpearman correlation between numeric grade and stage:",
        round(
            grade_stage["stage"].corr(
                grade_stage["grade"], method="spearman"
            ), 4
        )
    )

    grade_stage.to_csv(
        OUTPUT_DIR / "experiment8a_grade_stage_rows.csv",
        index=False,
    )

    section("6. TIME-INDEXED FEATURE REVIEW")

    time_indexed = [
        "ALT4", "ALT 12", "ALT 24", "ALT 36", "ALT 48",
        "ALT after 24 w", "RNA Base", "RNA 4", "RNA 12",
        "RNA EOT", "RNA EF",
    ]

    time_rows = []

    for feature in time_indexed:
        if feature not in df.columns:
            continue

        numeric = pd.to_numeric(df[feature], errors="coerce")

        row = {
            "feature": feature,
            "missing": int(df[feature].isna().sum()),
            "unique": int(numeric.nunique()),
            "minimum": numeric.min(),
            "median": numeric.median(),
            "maximum": numeric.max(),
        }
        time_rows.append(row)
        print(row)

    pd.DataFrame(time_rows).to_csv(
        OUTPUT_DIR / "experiment8a_time_indexed_audit.csv",
        index=False,
    )

    section("7. VERIFICATION SUMMARY")

    print("Official dataset stage interpretation to verify:")
    print("Stage 1: portal fibrosis without septa")
    print("Stage 2: few septa")
    print("Stage 3: many septa without cirrhosis")
    print("Stage 4: cirrhosis")
    print("\nImportant limitations:")
    print("- This audit cannot independently verify biopsy diagnoses.")
    print("- Grading is not interchangeable with staging.")
    print("- AST 1 and ALT 1 are described as ratios in the dataset docs.")
    print("- Do not calculate clinical FIB-4 from these fields without")
    print("  confirming units, definitions and suitability.")
    print("- Later ALT/RNA measurements may cause temporal leakage.")
    print("- Dataset coding alone does not establish clinical validity.")

    print("\nAudit files saved in:", OUTPUT_DIR.resolve())


if __name__ == "__main__":
    main()
