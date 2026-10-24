
import pandas as pd
import numpy as np
from scipy.stats import spearmanr, pearsonr, kruskal
from pathlib import Path

# ============================================================
# EXPERIMENT 8E: FIB-4 AND LIVER STIFFNESS ASSOCIATION
# ============================================================

print("=" * 72)
print("EXPERIMENT 8E: FIB-4 AND LIVER STIFFNESS ASSOCIATION")
print("=" * 72)

INPUT_FILE = Path("outputs/nhanes_8c_complete_exams.csv")
OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)


df = pd.read_csv(INPUT_FILE)

# Keep adults with valid FIB-4 inputs and recorded liver stiffness.
required = [
    "age_years_nhanes",
    "fib4",
    "liver_stiffness_median_kpa",
]

missing = [col for col in required if col not in df.columns]
if missing:
    raise ValueError(
        f"Missing columns: {missing}\n"
        f"Available columns: {df.columns.tolist()}"
    )

df = df[required].copy()

 

missing = [col for col in required if col not in df.columns]
if missing:
    raise ValueError(
        f"Missing required columns: {missing}\n"
        f"Available columns: {df.columns.tolist()}"
    )

df = df[required].copy()

for col in required:
    df[col] = pd.to_numeric(df[col], errors="coerce")

df = df.replace([np.inf, -np.inf], np.nan)
df = df.dropna(subset=required)

print(f"\nParticipants analysed: {len(df):,}")
print(f"Missing required values after filtering: {df[required].isna().sum().sum()}")

# ------------------------------------------------------------
# 1. Overall association
# ------------------------------------------------------------

spearman_r, spearman_p = spearmanr(
    df["fib4"],
    df["liver_stiffness_median_kpa"]
)

pearson_r, pearson_p = pearsonr(
    df["fib4"],
    df["liver_stiffness_median_kpa"]
)

print("\n1. OVERALL ASSOCIATION")
print("-" * 72)
print(f"Spearman correlation: {spearman_r:.4f}")
print(f"Spearman p-value:     {spearman_p:.6g}")
print(f"Pearson correlation:  {pearson_r:.4f}")
print(f"Pearson p-value:      {pearson_p:.6g}")

# ------------------------------------------------------------
# 2. Descriptive statistics by age group
# ------------------------------------------------------------

df["age_group"] = pd.cut(
    df["age_years_nhanes"],
    bins=[17, 29, 39, 49, 59, 69, 80],
    labels=["18-29", "30-39", "40-49", "50-59", "60-69", "70-80"],
    include_lowest=True
)

age_summary = (
    df.groupby("age_group", observed=False)
    .agg(
        participants=("fib4", "size"),
        median_fib4=("fib4", "median"),
        median_stiffness_kpa=("liver_stiffness_median_kpa", "median"),
        mean_fib4=("fib4", "mean"),
        mean_stiffness_kpa=("liver_stiffness_median_kpa", "mean"),
    )
    .reset_index()
)

print("\n2. SUMMARY BY AGE GROUP")
print("-" * 72)
print(age_summary.to_string(index=False))

# ------------------------------------------------------------
# 3. Association within age groups
# ------------------------------------------------------------

print("\n3. SPEARMAN CORRELATION WITHIN AGE GROUPS")
print("-" * 72)

age_correlations = []

for age_group, group in df.groupby("age_group", observed=False):
    if len(group) >= 10:
        rho, p_value = spearmanr(
            group["fib4"],
            group["liver_stiffness_median_kpa"]
        )
        age_correlations.append({
            "age_group": str(age_group),
            "participants": len(group),
            "spearman_rho": rho,
            "p_value": p_value,
        })

age_corr_df = pd.DataFrame(age_correlations)

if not age_corr_df.empty:
    print(age_corr_df.to_string(index=False))
else:
    print("No age group had at least 10 participants.")

# ------------------------------------------------------------
# 4. Save results
# ------------------------------------------------------------

age_summary.to_csv(
    OUTPUT_DIR / "nhanes_8e_age_group_summary.csv",
    index=False
)

age_corr_df.to_csv(
    OUTPUT_DIR / "nhanes_8e_age_group_correlations.csv",
    index=False
)

overall_results = pd.DataFrame([{
    "participants": len(df),
    "spearman_rho": spearman_r,
    "spearman_p_value": spearman_p,
    "pearson_r": pearson_r,
    "pearson_p_value": pearson_p,
}])

overall_results.to_csv(
    OUTPUT_DIR / "nhanes_8e_overall_association.csv",
    index=False
)

print("\n4. FILES SAVED")
print("-" * 72)
print("outputs/nhanes_8e_age_group_summary.csv")
print("outputs/nhanes_8e_age_group_correlations.csv")
print("outputs/nhanes_8e_overall_association.csv")

print("\nExperiment 8E completed.")
print("=" * 72)
