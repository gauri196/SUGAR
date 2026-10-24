
import pandas as pd
import numpy as np
from pathlib import Path

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

print("=" * 72)
print("EXPERIMENT 8H: FAIR MODEL COMPARISON")
print("=" * 72)

INPUT_FILE = Path("outputs/nhanes_8c_complete_exams.csv")
OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)

df = pd.read_csv(INPUT_FILE)

required = [
    "SEQN",
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

for col in required:
    df[col] = pd.to_numeric(df[col], errors="coerce")

df = df.replace([np.inf, -np.inf], np.nan)

# Fair comparison: use only participants with all required values.
df = df.dropna(subset=required)

df = df[
    (df["age_years_nhanes"] >= 18)
    & (df["fib4"] > 0)
    & (df["liver_stiffness_median_kpa"] > 0)
    & (df["liver_cap_median_dbm"] > 0)
].copy()

df["log_stiffness"] = np.log(df["liver_stiffness_median_kpa"])

print(f"\nCommon complete-case cohort: {len(df):,}")

if len(df) < 100:
    raise ValueError("Too few participants for a meaningful comparison.")

# Same participants in train/test for every model.
train_idx, test_idx = train_test_split(
    df.index,
    test_size=0.20,
    random_state=42,
)

train = df.loc[train_idx].copy()
test = df.loc[test_idx].copy()

feature_sets = {
    "Model 1: Age + sex": [
        "age_years_nhanes",
        "sex_code_nhanes",
    ],
    "Model 2: Age + sex + FIB-4": [
        "age_years_nhanes",
        "sex_code_nhanes",
        "fib4",
    ],
    "Model 3: Age + sex + FIB-4 + CAP": [
        "age_years_nhanes",
        "sex_code_nhanes",
        "fib4",
        "liver_cap_median_dbm",
    ],
}

results = []
all_predictions = []

for model_name, features in feature_sets.items():
    numeric_features = [
        c for c in features if c != "sex_code_nhanes"
    ]
    categorical_features = [
        "sex_code_nhanes"
    ]

    numeric_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])

    categorical_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore")),
    ])

    preprocessing = ColumnTransformer([
        ("numeric", numeric_pipeline, numeric_features),
        ("categorical", categorical_pipeline, categorical_features),
    ])

    model = Pipeline([
        ("preprocessing", preprocessing),
        ("regression", LinearRegression()),
    ])

    X_train = train[features]
    y_train = train["log_stiffness"]
    X_test = test[features]
    y_test = test["log_stiffness"]

    model.fit(X_train, y_train)
    predicted_log = model.predict(X_test)

    actual_kpa = np.exp(y_test.to_numpy())
    predicted_kpa = np.exp(predicted_log)

    mae = mean_absolute_error(actual_kpa, predicted_kpa)
    rmse = np.sqrt(mean_squared_error(actual_kpa, predicted_kpa))
    r2 = r2_score(y_test, predicted_log)

    results.append({
        "model": model_name,
        "training_participants": len(train),
        "test_participants": len(test),
        "test_mae_kpa": mae,
        "test_rmse_kpa": rmse,
        "test_r2_log_scale": r2,
    })

    for seqn, actual, predicted in zip(
        test["SEQN"].to_numpy(),
        actual_kpa,
        predicted_kpa,
    ):
        all_predictions.append({
            "SEQN": seqn,
            "model": model_name,
            "actual_stiffness_kpa": actual,
            "predicted_stiffness_kpa": predicted,
        })

    print(f"\n{model_name}")
    print(f"Training participants: {len(train):,}")
    print(f"Test participants:     {len(test):,}")
    print(f"Test MAE:              {mae:.4f} kPa")
    print(f"Test RMSE:             {rmse:.4f} kPa")
    print(f"Test R-squared:        {r2:.4f} (log scale)")

results_df = pd.DataFrame(results)

# Percentage change relative to Model 1.
baseline_mae = results_df.loc[0, "test_mae_kpa"]
baseline_rmse = results_df.loc[0, "test_rmse_kpa"]

results_df["mae_improvement_vs_model1_pct"] = (
    (baseline_mae - results_df["test_mae_kpa"])
    / baseline_mae * 100
)

results_df["rmse_improvement_vs_model1_pct"] = (
    (baseline_rmse - results_df["test_rmse_kpa"])
    / baseline_rmse * 100
)

results_df.to_csv(
    OUTPUT_DIR / "nhanes_8h_fair_model_comparison.csv",
    index=False,
)

pd.DataFrame(all_predictions).to_csv(
    OUTPUT_DIR / "nhanes_8h_test_predictions.csv",
    index=False,
)

# Save the exact shared test IDs for reproducibility.
test[["SEQN"]].to_csv(
    OUTPUT_DIR / "nhanes_8h_test_participant_ids.csv",
    index=False,
)

print("\n" + "=" * 72)
print("MODEL COMPARISON SUMMARY")
print("=" * 72)
print(results_df.to_string(index=False, float_format=lambda x: f"{x:.4f}"))

print("\nSaved files:")
print("outputs/nhanes_8h_fair_model_comparison.csv")
print("outputs/nhanes_8h_test_predictions.csv")
print("outputs/nhanes_8h_test_participant_ids.csv")

print("\nExperiment 8H completed.")
print("=" * 72)
