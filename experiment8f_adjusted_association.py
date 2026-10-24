
import pandas as pd
import numpy as np
from pathlib import Path
from scipy.stats import spearmanr
import statsmodels.formula.api as smf

print("=" * 72)
print("EXPERIMENT 8F: AGE-ADJUSTED ASSOCIATION ANALYSIS")
print("=" * 72)

INPUT_FILE = Path("outputs/nhanes_8c_complete_exams.csv")
OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)

df = pd.read_csv(INPUT_FILE)

# Select variables that actually exist in the dataset.
required = [
    "age_years_nhanes",
    "sex_code_nhanes",
    "fib4",
    "liver_stiffness_median_kpa",
    "liver_cap_median_dbm",
]

missing = [col for col in required if col not in df.columns]
if missing:
    raise ValueError(f"Missing columns: {missing}")

df = df[required].copy()

# Convert values to numeric and remove invalid observations.
for col in required:
    df[col] = pd.to_numeric(df[col], errors="coerce")

df = df.replace([np.inf, -np.inf], np.nan)
df = df.dropna(
    subset=[
        "age_years_nhanes",
        "sex_code_nhanes",
        "fib4",
        "liver_stiffness_median_kpa",
    ]
)

# Restrict to adults with valid measurements.
df = df[
    (df["age_years_nhanes"] >= 18)
    & (df["liver_stiffness_median_kpa"] > 0)
    & (df["fib4"] > 0)
].copy()

print(f"\nParticipants in primary analysis: {len(df):,}")

# Log-transform right-skewed measurements for regression.
# log1p is defined even if a non-positive value occurs, though
# the primary filters above require positive FIB-4 and stiffness.
df["log_stiffness"] = np.log(df["liver_stiffness_median_kpa"])
df["log_fib4"] = np.log(df["fib4"])

# Treat sex code as categorical, not as a continuous quantity.
df["sex_code_nhanes"] = df["sex_code_nhanes"].astype("category")

# 1. Reproduce the unadjusted rank correlation.
rho, p_value = spearmanr(
    df["fib4"],
    df["liver_stiffness_median_kpa"]
)

print("\n1. UNADJUSTED SPEARMAN ASSOCIATION")
print("-" * 72)
print(f"Spearman rho: {rho:.4f}")
print(f"P-value:      {p_value:.6g}")

# 2. Regression models.
# The coefficient is on log(stiffness); this is an association,
# not a diagnostic accuracy estimate.
models = {
    "Model 1: FIB-4 only": "log_stiffness ~ log_fib4",
    "Model 2: Adjusted for age and sex":
        "log_stiffness ~ log_fib4 + age_years_nhanes + C(sex_code_nhanes)",
}

# CAP model is a secondary complete-case analysis.
cap_df = df.dropna(subset=["liver_cap_median_dbm"]).copy()
if len(cap_df) >= 100:
    models["Model 3: Also adjusted for CAP"] = (
        "log_stiffness ~ log_fib4 + age_years_nhanes "
        "+ C(sex_code_nhanes) + liver_cap_median_dbm"
    )

results = []

print("\n2. REGRESSION MODELS")
print("-" * 72)

for name, formula in models.items():
    if "CAP" in name:
        model_df = cap_df
    else:
        model_df = df

    fitted = smf.ols(formula, data=model_df).fit(cov_type="HC3")

    term = "log_fib4"
    coefficient = fitted.params.get(term, np.nan)
    p = fitted.pvalues.get(term, np.nan)
    ci_low, ci_high = fitted.conf_int().loc[term].tolist()

    results.append({
        "model": name,
        "participants": int(fitted.nobs),
        "log_fib4_coefficient": coefficient,
        "robust_ci_lower": ci_low,
        "robust_ci_upper": ci_high,
        "p_value": p,
        "r_squared": fitted.rsquared,
    })

    print(f"\n{name}")
    print(f"Participants: {int(fitted.nobs):,}")
    print(f"FIB-4 coefficient (log scale): {coefficient:.5f}")
    print(f"95% robust CI: [{ci_low:.5f}, {ci_high:.5f}]")
    print(f"P-value: {p:.6g}")
    print(f"R-squared: {fitted.rsquared:.4f}")

results_df = pd.DataFrame(results)
results_df.to_csv(
    OUTPUT_DIR / "nhanes_8f_adjusted_models.csv",
    index=False
)

# 3. Save the analytic cohort for reproducibility.
df.to_csv(
    OUTPUT_DIR / "nhanes_8f_analysis_cohort.csv",
    index=False
)

print("\n3. FILES SAVED")
print("-" * 72)
print("outputs/nhanes_8f_adjusted_models.csv")
print("outputs/nhanes_8f_analysis_cohort.csv")

print("\nExperiment 8F completed.")
print("=" * 72)
