
from pathlib import Path
import pandas as pd
import json

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

files = [
    DATA_DIR / "HCV-Egy-Data.csv",
    DATA_DIR / "cirrhosis.csv",
]

report = {}

for path in files:
    if not path.exists():
        print(f"\nNOT FOUND: {path.name}")
        continue

    df = pd.read_csv(path)
    df.columns = df.columns.astype(str).str.strip()

    print("\n" + "=" * 65)
    print(f"DATASET: {path.name}")
    print("=" * 65)
    print("Shape:", df.shape)
    print("\nColumns:")
    print(df.columns.tolist())
    print("\nMissing values:")
    print(df.isna().sum().to_string())
    print("\nDuplicate rows:", int(df.duplicated().sum()))

    report[path.name] = {
        "rows": int(df.shape[0]),
        "columns_count": int(df.shape[1]),
        "columns": df.columns.tolist(),
        "missing_values": {
            str(k): int(v)
            for k, v in df.isna().sum().items()
        },
        "duplicate_rows": int(df.duplicated().sum()),
    }

output = BASE_DIR / "dataset_audit.json"
output.write_text(json.dumps(report, indent=2), encoding="utf-8")

print(f"\nAudit saved to: {output}")
