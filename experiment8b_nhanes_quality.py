
from pathlib import Path
import pandas as pd

file_path = Path("data/P_LUX.XPT")
if not file_path.exists():
    file_path = Path("data/P_LUX.xpt")

df = pd.read_sas(file_path, format="xport")

print("=" * 65)
print("EXPERIMENT 8B: NHANES ELASTOGRAPHY QUALITY AUDIT")
print("=" * 65)

print("\n1. EXAM STATUS")
print(df["LUAXSTAT"].value_counts(dropna=False).sort_index())

print("\n2. EXAM STATUS AND STIFFNESS AVAILABILITY")
print(pd.crosstab(
    df["LUAXSTAT"],
    df["LUXSMED"].notna(),
    margins=True
).to_string())

print("\n3. COMPLETE EXAMS")
complete = df[df["LUAXSTAT"] == 1].copy()
print("Complete exams:", len(complete))
print("Complete exams with stiffness:", complete["LUXSMED"].notna().sum())
print("Complete exams missing stiffness:", complete["LUXSMED"].isna().sum())

print("\n4. STIFFNESS DISTRIBUTION IN COMPLETE EXAMS")
stiffness = complete["LUXSMED"].dropna()
print(stiffness.describe().to_string())

print("\n5. QUALITY MEASURES")
for col in ["LUANMVGP", "LUANMTGP", "LUXSIQR", "LUXSIQRM", "LUXCAPM"]:
    if col in complete.columns:
        print(f"\n{col}:")
        print(complete[col].describe().to_string())

print("\n6. EXPORT PRELIMINARY COMPLETE-EXAM DATA")
out = Path("outputs")
out.mkdir(exist_ok=True)

complete.to_csv(
    out / "nhanes_lux_complete_exams_preliminary.csv",
    index=False
)

print("\nSaved: outputs/nhanes_lux_complete_exams_preliminary.csv")
print("This is a preliminary extract, not the final quality-filtered cohort.")
