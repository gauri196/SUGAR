
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import kruskal, chi2_contingency

# ============================================================
# EXPERIMENT 7: STATISTICAL FEATURE-STAGE ASSOCIATION
# ============================================================

DATA_PATH = Path("data/HCV-Egy-Data.csv")
OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TARGET = "Baselinehistological staging"

# Continuous/numeric measurements to investigate.
# These are tested for association, not assumed to be predictors.
CONTINUOUS_FEATURES = [
    "Age",
    "BMI",
    "WBC",
    "RBC",
    "HGB",
    "Plat",
    "AST 1",
    "ALT 1",
]

# Categorical fields, including demographic and symptom variables.
CATEGORICAL_FEATURES = [
    "Gender",
    "Fever",
    "Nausea/Vomting",
    "Headache",
    "Diarrhea",
    "Fatigue & generalized bone ache",
    "Jaundice",
    "Epigastric pain",
]

STAGES = [1, 2, 3, 4]


def benjamini_hochberg(p_values):
    """Return Benjamini-Hochberg adjusted p-values."""
    p_values = np.asarray(p_values, dtype=float)
    n = len(p_values)

    if n == 0:
        return np.array([])

    order = np.argsort(p_values)
    sorted_p = p_values[order]
    adjusted_sorted = sorted_p * n / np.arange(1, n + 1)

    # Adjusted values must be monotonic.
    adjusted_sorted = np.minimum.accumulate(
        adjusted_sorted[::-1]
    )[::-1]

    adjusted_sorted = np.clip(adjusted_sorted, 0, 1)
    adjusted = np.empty(n)
    adjusted[order] = adjusted_sorted

    return adjusted


def main():
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found: {DATA_PATH}\n"
            "Run this script from your project root folder."
        )

    df = pd.read_csv(DATA_PATH)
    df.columns = df.columns.str.strip()

    required = (
        [TARGET]
        + CONTINUOUS_FEATURES
        + CATEGORICAL_FEATURES
    )

    missing_columns = [
        col for col in required if col not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Required columns are missing: {missing_columns}"
        )

    # Keep only records with one of the four known stages.
    df[TARGET] = pd.to_numeric(df[TARGET], errors="coerce")
    df = df[df[TARGET].isin(STAGES)].copy()
    df[TARGET] = df[TARGET].astype(int)

    print("=" * 70)
    print("EXPERIMENT 7: FEATURE-STAGE ASSOCIATION")
    print("=" * 70)
    print("Records analysed:", len(df))
    print("Stage counts:")
    print(df[TARGET].value_counts().sort_index().to_string())

    # --------------------------------------------------------
    # 1. CONTINUOUS FEATURES: KRUSKAL-WALLIS TEST
    # --------------------------------------------------------

    continuous_results = []
    stage_summary_rows = []

    print("\n1. CONTINUOUS FEATURES")
    print("-" * 70)

    for feature in CONTINUOUS_FEATURES:
        values = pd.to_numeric(df[feature], errors="coerce")

        groups = [
            values[df[TARGET] == stage].dropna().to_numpy()
            for stage in STAGES
        ]
        groups = [group for group in groups if len(group) > 0]

        if len(groups) < 2:
            print(f"Skipping {feature}: insufficient data.")
            continue

        h_stat, p_value = kruskal(*groups)

        total_n = sum(len(group) for group in groups)
        k = len(groups)

        # Epsilon-squared effect size for Kruskal-Wallis.
        epsilon_squared = max(
            0.0, (h_stat - k + 1) / (total_n - k)
        )

        continuous_results.append({
            "feature": feature,
            "test": "Kruskal-Wallis",
            "n": total_n,
            "H_statistic": h_stat,
            "p_value": p_value,
            "epsilon_squared": epsilon_squared,
        })

        for stage in STAGES:
            group = values[df[TARGET] == stage].dropna()

            stage_summary_rows.append({
                "feature": feature,
                "stage": stage,
                "n": len(group),
                "mean": group.mean(),
                "median": group.median(),
                "std": group.std(),
            })

        print(
            f"{feature:8s} | H={h_stat:9.4f} | "
            f"p={p_value:.6g} | "
            f"epsilon²={epsilon_squared:.4f}"
        )

    continuous_df = pd.DataFrame(continuous_results)

    if not continuous_df.empty:
        continuous_df["adjusted_p_value_BH"] = (
            benjamini_hochberg(continuous_df["p_value"])
        )
        continuous_df = continuous_df.sort_values(
            "adjusted_p_value_BH"
        )

    pd.DataFrame(stage_summary_rows).to_csv(
        OUTPUT_DIR / "experiment7_continuous_by_stage.csv",
        index=False,
    )

    continuous_df.to_csv(
        OUTPUT_DIR / "experiment7_continuous_tests.csv",
        index=False,
    )

    # --------------------------------------------------------
    # 2. CATEGORICAL FEATURES: CHI-SQUARE TEST
    # --------------------------------------------------------

    categorical_results = []

    print("\n2. CATEGORICAL FEATURES")
    print("-" * 70)

    for feature in CATEGORICAL_FEATURES:
        subset = df[[feature, TARGET]].dropna()

        table = pd.crosstab(subset[feature], subset[TARGET])

        if table.shape[0] < 2 or table.shape[1] < 2:
            print(f"Skipping {feature}: insufficient categories.")
            continue

        chi2, p_value, degrees_freedom, expected = (
            chi2_contingency(table, correction=False)
        )

        n = table.to_numpy().sum()
        rows, columns = table.shape
        denominator = n * min(rows - 1, columns - 1)

        cramers_v = (
            np.sqrt(chi2 / denominator)
            if denominator > 0 else np.nan
        )

        minimum_expected = expected.min()

        categorical_results.append({
            "feature": feature,
            "test": "Chi-square",
            "n": int(n),
            "chi2_statistic": chi2,
            "degrees_freedom": degrees_freedom,
            "p_value": p_value,
            "cramers_v": cramers_v,
            "minimum_expected_cell_count": minimum_expected,
            "expected_count_below_5": bool(
                (expected < 5).any()
            ),
        })

        print(
            f"{feature[:29]:29s} | chi²={chi2:9.4f} | "
            f"p={p_value:.6g} | "
            f"Cramer's V={cramers_v:.4f} | "
            f"expected<5={bool((expected < 5).any())}"
        )

        # Save each contingency table for inspection.
        safe_name = (
            feature.lower()
            .replace("/", "_")
            .replace(" ", "_")
            .replace("&", "and")
        )

        table.to_csv(
            OUTPUT_DIR / f"experiment7_crosstab_{safe_name}.csv"
        )

    categorical_df = pd.DataFrame(categorical_results)

    if not categorical_df.empty:
        categorical_df["adjusted_p_value_BH"] = (
            benjamini_hochberg(categorical_df["p_value"])
        )
        categorical_df = categorical_df.sort_values(
            "adjusted_p_value_BH"
        )

    categorical_df.to_csv(
        OUTPUT_DIR / "experiment7_categorical_tests.csv",
        index=False,
    )

    # --------------------------------------------------------
    # 3. COMBINED RESULTS
    # --------------------------------------------------------

    combined_rows = []

    for _, row in continuous_df.iterrows():
        combined_rows.append({
            "feature": row["feature"],
            "feature_type": "continuous",
            "test": row["test"],
            "p_value": row["p_value"],
            "adjusted_p_value_BH": row["adjusted_p_value_BH"],
            "effect_size_name": "epsilon_squared",
            "effect_size": row["epsilon_squared"],
        })

    for _, row in categorical_df.iterrows():
        combined_rows.append({
            "feature": row["feature"],
            "feature_type": "categorical",
            "test": row["test"],
            "p_value": row["p_value"],
            "adjusted_p_value_BH": row["adjusted_p_value_BH"],
            "effect_size_name": "cramers_v",
            "effect_size": row["cramers_v"],
        })

    combined_df = pd.DataFrame(combined_rows)

    if not combined_df.empty:
        combined_df = combined_df.sort_values(
            "adjusted_p_value_BH"
        )

    combined_df.to_csv(
        OUTPUT_DIR / "experiment7_all_associations.csv",
        index=False,
    )

    print("\n" + "=" * 70)
    print("TOP FEATURES BY ADJUSTED P-VALUE")
    print("=" * 70)

    if combined_df.empty:
        print("No valid test results were produced.")
    else:
        print(
            combined_df[
                [
                    "feature",
                    "feature_type",
                    "p_value",
                    "adjusted_p_value_BH",
                    "effect_size_name",
                    "effect_size",
                ]
            ].round(5).to_string(index=False)
        )

    print("\nInterpretation guidance:")
    print("- Adjusted p < 0.05 suggests statistical evidence of association.")
    print("- Effect sizes help assess the strength of association.")
    print("- Statistical association does not prove predictive usefulness.")
    print("- Small expected cell counts weaken chi-square approximations.")
    print("- These tests do not establish causation or clinical validity.")
    print("- Histological grading is intentionally excluded.")
    print("- Post-baseline ALT/RNA fields are intentionally excluded.")

    print("\nFiles saved in:", OUTPUT_DIR)
    print("1. experiment7_continuous_tests.csv")
    print("2. experiment7_continuous_by_stage.csv")
    print("3. experiment7_categorical_tests.csv")
    print("4. experiment7_all_associations.csv")
    print("5. experiment7_crosstab_*.csv")


if __name__ == "__main__":
    main()
