
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
print("EXPERIMENT 8G: HELD-OUT PREDICTIVE PERFORMANCE")
print("=" * 72)

INPUT_FILE = Path("outputs/nhanes_8c_complete_exams.csv")
OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)

df = pd.read_csv(INPUT_FILE)

# Use only adults with valid stiffness and FIB-4.
required = [
    "SEQN",
    "age_years_nhanes",
    "sex_code_nhanes",
    "fib4",
    "liver_stiffness_median_kpa",
    "liver_cap_median_dbm",
]

missing = [c for c in required if c not in df.columns]
if missing:
    raise ValueError(f"Missing columns: {missing}")

df = df[required].copy()

for col in required:
    df[col] = pd.to_numeric(df[col], errors="coerce")

df = df.replace([np.inf, -np.inf], np.nan)

df = df[
    (df["age_years_nhanes"] >= 18)
    & (df["fib4"] > 0)
    & (df["liver_stiffness_median_kpa"] > 0)
].copy()

print(f"\nEligible participants before split: {len(df):,}")

# Keep CAP-missing participants for Models 1 and 2.
# Model 3 will use the same held-out participants with observed CAP.
train_ids, test_ids = train_test_split(
    df["SEQN"].to_numpy(),
    test_size=0.20,
    random_state=42,
)

train = df[df["SEQN"].isin(train_ids)].copy()
test = df[df["SEQN"].isin(test_ids)].copy()

# The target is log stiffness to reduce skew.
train["target_log_stiffness"] = np.log(train["liver_stiffness_median_kpa"])
test["target_log_stiffness"] = np.log(test["liver_stiffness_median_kpa"])

feature_sets = {
    "Model 1: Age + sex": [
        "age_years_nhanes",
        "sex_code_nhanes",
    ],
    "Model 2: FIB-4 + age + sex": [
        "fib4",
        "age_years_nhanes",
        "sex_code_nhanes",
    ],
    "Model 3: FIB-4 + age + sex + CAP": [
        "fib4",
        "age_years_nhanes",
        "sex_code_nhanes",
        "liver_cap_median_dbm",
    ],
}

results = []
predictions = []

for model_name, features in feature_sets.items():
    train_model = train.dropna(
        subset=features + ["target_log_stiffness"]
    ).copy()
    test_model = test.dropna(
        subset=features + ["target_log_stiffness"]
    ).copy()

    if len(train_model) == 0 or len(test_model) == 0:
        print(f"\nSkipping {model_name}: no usable rows.")
        continue

    numeric_features = [
        c for c in features if c != "sex_code_nhanes"
    ]
    categorical_features = [
        c for c in features if c == "sex_code_nhanes"
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

    X_train = train_model[features]
    y_train = train_model["target_log_stiffness"]
    X_test = test_model[features]
    y_test = test_model["target_log_stiffness"]

    model.fit(X_train, y_train)
    pred_log = model.predict(X_test)

    # Back-transform predictions for metrics in kPa.
    actual_kpa = np.exp(y_test.to_numpy())
    predicted_kpa = np.exp(pred_log)

    mae = mean_absolute_error(actual_kpa, predicted_kpa)
    rmse = np.sqrt(mean_squared_error(actual_kpa, predicted_kpa))
    r2 = r2_score(y_test, pred_log)

    results.append({
        "model": model_name,
        "training_participants": len(train_model),
        "test_participants": len(test_model),
        "test_mae_kpa": mae,
        "test_rmse_kpa": rmse,
        "test_r2_log_scale": r2,
    })

    for seqn, actual, predicted in zip(
        test_model["SEQN"].to_numpy(),
        actual_kpa,
        predicted_kpa,
    ):
        predictions.append({
            "SEQN": seqn,
            "model": model_name,
            "actual_stiffness_kpa": actual,
            "predicted_stiffness_kpa": predicted,
        })

    print(f"\n{model_name}")
    print(f"Training participants: {len(train_model):,}")
    print(f"Test participants:     {len(test_model):,}")
    print(f"Test MAE:              {mae:.4f} kPa")
    print(f"Test RMSE:             {rmse:.4f} kPa")
    print(f"Test R-squared:        {r2:.4f} (log scale)")

results_df = pd.DataFrame(results)
predictions_df = pd.DataFrame(predictions)

results_df.to_csv(
    OUTPUT_DIR / "nhanes_8g_predictive_performance.csv",
    index=False
)
predictions_df.to_csv(
    OUTPUT_DIR / "nhanes_8g_test_predictions.csv",
    index=False
)

print("\nSaved:")
print("outputs/nhanes_8g_predictive_performance.csv")
print("outputs/nhanes_8g_test_predictions.csv")
print("\nExperiment 8G completed.")
print("=" * 72)
