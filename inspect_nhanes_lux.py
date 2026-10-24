
from pathlib import Path
import pandas as pd

file_path = Path("data/P_LUX.XPT")

if not file_path.exists():
    raise FileNotFoundError(
        f"File not found: {file_path.resolve()}\n"
        "Check that P_LUX.XPT is inside the data folder."
    )

df = pd.read_sas(file_path, format="xport")

print("=" * 65)
print("NHANES LIVER ELASTOGRAPHY DATA AUDIT")
print("=" * 65)

print(f"\nFile: {file_path.resolve()}")
print(f"Rows: {df.shape[0]}")
print(f"Columns: {df.shape[1]}")

print("\nCOLUMN NAMES")
print("-" * 65)
for column in df.columns:
    print(column)

print("\nMISSING VALUES")
print("-" * 65)
print(df.isnull().sum().to_string())

print("\nKEY MEASUREMENT SUMMARY")
print("-" * 65)

key_columns = [
    "SEQN",
    "LUAXSTAT",
    "LUANMVGP",
    "LUANMTGP",
    "LUXSMED",
    "LUXSIQR",
    "LUXSIQRM",
    "LUXCAPM",
    "LUXCPIQR",
]

for column in key_columns:
    if column in df.columns:
        print(f"\n{column}")
        print(df[column].describe().to_string())
        print("Unique values:", df[column].nunique())

if "SEQN" in df.columns:
    print("\nDuplicate participant IDs:", df["SEQN"].duplicated().sum())

output_path = Path("outputs")
output_path.mkdir(exist_ok=True)

df.head(20).to_csv(
    output_path / "nhanes_lux_preview.csv",
    index=False
)

print("\nPreview saved to outputs/nhanes_lux_preview.csv")
print("\nAudit completed.")
