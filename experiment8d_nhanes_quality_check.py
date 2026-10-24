from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "outputs"
INPUT_FILE = OUTPUT_DIR / "nhanes_8c_complete_exams.csv"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

if not INPUT_FILE.exists():
    raise FileNotFoundError(
        f"Could not find {INPUT_FILE}. Run experiment8c_merge_nhanes.py first."
    )

df = pd.read_csv(INPUT_FILE)

needed = [
    "age_years_nhanes", "ast_u_l", "alt_u_l", "platelets_10e9_l",
    "fib4", "liver_stiffness_median_kpa", "liver_stiffness_iqr_kpa",
    "liver_stiffness_iqr_median_ratio", "liver_cap_median_dbm",
    "liver_cap_iqr_dbm", "valid_stiffness_measurement_count",
    "total_stiffness_measurement_count", "elastography_exam_status"
]
missing_cols = [c for c in needed if c not in df.columns]
if missing_cols:
    raise KeyError(f"Input file is missing expected columns: {missing_cols}")

for c in needed:
    df[c] = pd.to_numeric(df[c], errors="coerce")

# Recalculate FIB-4 from source values to independently verify the saved field.
adult = df.loc[
    (df["elastography_exam_status"] == 1)
    & (df["age_years_nhanes"] >= 18)
    & df["liver_stiffness_median_kpa"].notna()
].copy()

valid = (
    adult["ast_u_l"].notna() & adult["alt_u_l"].notna()
    & adult["platelets_10e9_l"].notna()
    & (adult["ast_u_l"] > 0) & (adult["alt_u_l"] > 0)
    & (adult["platelets_10e9_l"] > 0)
)
adult["fib4_recalculated"] = np.nan
adult.loc[valid, "fib4_recalculated"] = (
    adult.loc[valid, "age_years_nhanes"] * adult.loc[valid, "ast_u_l"]
    / (
        adult.loc[valid, "platelets_10e9_l"]
        * np.sqrt(adult.loc[valid, "alt_u_l"])
    )
)

both = adult.loc[
    adult["fib4_recalculated"].notna()
    & adult["liver_stiffness_median_kpa"].notna()
].copy()

print("=" * 72)
print("EXPERIMENT 8D: NHANES DATA QUALITY + FIB-4/STIFFNESS OVERLAP")
print("=" * 72)
print(f"Complete exams: {len(df):,}")
print(f"Adults 18+ with recorded stiffness: {len(adult):,}")
print(f"Adults with valid FIB-4 and stiffness (intersection): {len(both):,}")

# Check the FIB-4 formula against the existing saved value.
compare = adult["fib4"].notna() & adult["fib4_recalculated"].notna()
if compare.any():
    max_diff = (adult.loc[compare, "fib4"] - adult.loc[compare, "fib4_recalculated"]).abs().max()
    print(f"Maximum absolute difference vs saved FIB-4: {max_diff:.12g}")
else:
    print("No overlapping saved/recalculated FIB-4 values to compare.")

print("\n1. NUMERIC RANGE CHECKS")
range_cols = [
    "age_years_nhanes", "ast_u_l", "alt_u_l", "platelets_10e9_l",
    "fib4_recalculated", "liver_stiffness_median_kpa",
    "liver_stiffness_iqr_kpa", "liver_stiffness_iqr_median_ratio",
    "liver_cap_median_dbm", "liver_cap_iqr_dbm",
    "valid_stiffness_measurement_count", "total_stiffness_measurement_count"
]
print(both[range_cols].describe(percentiles=[.01, .05, .25, .5, .75, .95, .99]).round(3).to_string())

print("\n2. EXTREME-VALUE COUNTS (flags for review, not automatic deletion)")
checks = {
    "AST > 100 U/L": both["ast_u_l"] > 100,
    "ALT > 100 U/L": both["alt_u_l"] > 100,
    "platelets < 50 (10^9/L)": both["platelets_10e9_l"] < 50,
    "platelets > 600 (10^9/L)": both["platelets_10e9_l"] > 600,
    "FIB-4 > 3.25 (screening flag only)": both["fib4_recalculated"] > 3.25,
    "stiffness > 20 kPa": both["liver_stiffness_median_kpa"] > 20,
    "stiffness > 50 kPa": both["liver_stiffness_median_kpa"] > 50,
    "stiffness IQR/median > 30%": both["liver_stiffness_iqr_median_ratio"] > 30,
    "valid stiffness count < 10": both["valid_stiffness_measurement_count"] < 10,
}
for label, mask in checks.items():
    print(f"{label}: {int(mask.fillna(False).sum()):,}")