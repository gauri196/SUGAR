from pathlib import Path
import numpy as np
import pandas as pd

# Run from the project root:
# python experiment8c_merge_nhanes.py

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
OUTPUT_DIR = ROOT / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

FILES = {
    "lux": DATA_DIR / "P_LUX.xpt",
    "demo": DATA_DIR / "P_DEMO.xpt",
    "biopro": DATA_DIR / "P_BIOPRO.xpt",
    "cbc": DATA_DIR / "P_CBC.xpt",
}

def load_xpt(label, path):
    if not path.exists():
        raise FileNotFoundError(
            f"Missing file: {path}\nPut all four NHANES .xpt files in the data folder."
        )
    df = pd.read_sas(path, format="xport")
    if "SEQN" not in df.columns:
        raise KeyError(f"{path.name} does not contain the required SEQN column.")
    df["SEQN"] = pd.to_numeric(df["SEQN"], errors="coerce")
    duplicates = int(df["SEQN"].duplicated().sum())
    print(f"{label}: {len(df):,} rows x {len(df.columns)} columns; duplicate SEQN rows={duplicates}")
    if duplicates:
        raise ValueError(f"Duplicate SEQN values found in {path.name}; inspect before merging.")
    return df

print("=" * 72)
print("EXPERIMENT 8C: NHANES LIVER STIFFNESS + FIB-4 DATASET MERGE")
print("=" * 72)

lux = load_xpt("P_LUX", FILES["lux"])
demo = load_xpt("P_DEMO", FILES["demo"])
bio = load_xpt("P_BIOPRO", FILES["biopro"])
cbc = load_xpt("P_CBC", FILES["cbc"])

required = {
    "P_LUX": [
        "SEQN", "LUAXSTAT", "LUXSMED", "LUXSIQR", "LUXSIQRM",
        "LUXCAPM", "LUXCPIQR", "LUANMVGP", "LUANMTGP"
    ],
    "P_DEMO": ["SEQN", "RIDAGEYR", "RIAGENDR"],
    "P_BIOPRO": ["SEQN", "LBXSASSI", "LBXSATSI"],
    "P_CBC": ["SEQN", "LBXPLTSI"],
}
for label, df in [("P_LUX", lux), ("P_DEMO", demo), ("P_BIOPRO", bio), ("P_CBC", cbc)]:
    absent = [col for col in required[label] if col not in df.columns]
    if absent:
        raise KeyError(f"{label} is missing expected columns: {absent}")

# Keep only the columns needed for this initial audit.
merged = lux[required["P_LUX"]].merge(
    demo[required["P_DEMO"]], on="SEQN", how="left", validate="one_to_one"
)
merged = merged.merge(
    bio[required["P_BIOPRO"]], on="SEQN", how="left", validate="one_to_one"
)
merged = merged.merge(
    cbc[required["P_CBC"]], on="SEQN", how="left", validate="one_to_one"
)

merged = merged.rename(columns={
    "LUAXSTAT": "elastography_exam_status",
    "LUXSMED": "liver_stiffness_median_kpa",
    "LUXSIQR": "liver_stiffness_iqr_kpa",
    "LUXSIQRM": "liver_stiffness_iqr_median_ratio",
    "LUXCAPM": "liver_cap_median_dbm",
    "LUXCPIQR": "liver_cap_iqr_dbm",
    "LUANMVGP": "valid_stiffness_measurement_count",
    "LUANMTGP": "total_stiffness_measurement_count",
    "RIDAGEYR": "age_years_nhanes",
    "RIAGENDR": "sex_code_nhanes",
    "LBXSASSI": "ast_u_l",
    "LBXSATSI": "alt_u_l",
    "LBXPLTSI": "platelets_10e9_l",
})

numeric_cols = [
    "elastography_exam_status", "liver_stiffness_median_kpa",
    "liver_stiffness_iqr_kpa", "liver_stiffness_iqr_median_ratio",
    "liver_cap_median_dbm", "liver_cap_iqr_dbm",
    "valid_stiffness_measurement_count", "total_stiffness_measurement_count",
    "age_years_nhanes", "sex_code_nhanes", "ast_u_l", "alt_u_l",
    "platelets_10e9_l",
]
for col in numeric_cols:
    merged[col] = pd.to_numeric(merged[col], errors="coerce")

# NHANES P_LUX codebook: status 1 denotes a complete exam.
complete_exam = merged.loc[merged["elastography_exam_status"] == 1].copy()

# Calculate FIB-4 only when all inputs are valid.
valid_fib4_inputs = (
    complete_exam["age_years_nhanes"].notna()
    & complete_exam["ast_u_l"].notna()
    & complete_exam["alt_u_l"].notna()
    & complete_exam["platelets_10e9_l"].notna()
    & (complete_exam["age_years_nhanes"] >= 18)
    & (complete_exam["ast_u_l"] > 0)
    & (complete_exam["alt_u_l"] > 0)
    & (complete_exam["platelets_10e9_l"] > 0)
)

complete_exam["fib4"] = np.nan
valid_rows = complete_exam.loc[valid_fib4_inputs]
complete_exam.loc[valid_fib4_inputs, "fib4"] = (
    valid_rows["age_years_nhanes"] * valid_rows["ast_u_l"]
    / (
        valid_rows["platelets_10e9_l"]
        * np.sqrt(valid_rows["alt_u_l"])
    )
)

adult_stiffness = complete_exam.loc[
    (complete_exam["age_years_nhanes"] >= 18)
    & complete_exam["liver_stiffness_median_kpa"].notna()
].copy()

OUTPUT_DIR = Path(__file__).resolve().parent / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("\n1. MERGE CHECK")
print("-" * 60)
print(f"Merged participants: {len(merged):,}")
print(f"Unique SEQN: {merged['SEQN'].nunique():,}")
print(f"Complete exams: {len(complete_exam):,}")
print(f"Adults with recorded stiffness: {len(adult_stiffness):,}")
print(f"Adults with valid FIB-4 inputs: {int(valid_fib4_inputs.sum()):,}")

print("\n2. EXAM STATUS COUNTS")
print(merged["elastography_exam_status"].value_counts(dropna=False).sort_index())

report_cols = [
    "age_years_nhanes", "sex_code_nhanes", "ast_u_l", "alt_u_l",
    "platelets_10e9_l", "liver_stiffness_median_kpa", "liver_cap_median_dbm"
]
missing_report = pd.DataFrame({
    "non_missing": complete_exam[report_cols].notna().sum(),
    "missing": complete_exam[report_cols].isna().sum(),
    "missing_percent": (complete_exam[report_cols].isna().mean() * 100).round(2)
})

print("\n3. MISSINGNESS IN COMPLETE-EXAM COHORT")
print(missing_report.to_string())
missing_report.to_csv(OUTPUT_DIR / "nhanes_8c_missingness_report.csv")

summary_cols = [
    "age_years_nhanes", "ast_u_l", "alt_u_l", "platelets_10e9_l",
    "fib4", "liver_stiffness_median_kpa", "liver_cap_median_dbm"
]
print("\n4. ADULT COHORT SUMMARY")
print(adult_stiffness[summary_cols].describe().round(3).to_string())

merged.to_csv(OUTPUT_DIR / "nhanes_8c_merged_all_lux.csv", index=False)
complete_exam.to_csv(OUTPUT_DIR / "nhanes_8c_complete_exams.csv", index=False)
adult_stiffness.to_csv(
    OUTPUT_DIR / "nhanes_8c_adult_stiffness_preliminary.csv", index=False
)

print("\n5. SAVED OUTPUT FILES")
print("outputs/nhanes_8c_merged_all_lux.csv")
print("outputs/nhanes_8c_complete_exams.csv")
print("outputs/nhanes_8c_adult_stiffness_preliminary.csv")
print("outputs/nhanes_8c_missingness_report.csv")

print("\nNote: liver stiffness is a continuous measurement, not a biopsy-confirmed fibrosis stage.")
