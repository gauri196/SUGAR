
import json
from pathlib import Path

import numpy as np
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


# --------------------------------------------------
# 1. Configuration
# --------------------------------------------------

DATA_PATH = Path("data/HCV-Egy-Data.csv")
OUTPUT_DIR = Path("outputs")
RANDOM_STATE = 42
N_SPLITS = 10

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

BASELINE_FEATURES = [
    "Age",
    "BMI",
    "Plat",
    "AST 1",
    "ALT 1",
]

EXPANDED_FEATURES = BASELINE_FEATURES + [
    "WBC",
    "RBC",
    "HGB",
]


# --------------------------------------------------
# 2. Load and prepare the dataset
# --------------------------------------------------

df = pd.read_csv(DATA_PATH)

# Remove accidental leading/trailing spaces from column names.
df.columns = df.columns.str.strip()

target_column = "Baselinehistological staging"

required_columns = [target_column] + EXPANDED_FEATURES
missing_columns = [
    column for column in required_columns
    if column not in df.columns
]

if missing_columns:
    raise ValueError(
        f"Required columns not found: {missing_columns}"
    )

for column in EXPANDED_FEATURES + [target_column]:
    df[column] = pd.to_numeric(
        df[column], errors="coerce"
    )

# Exclude records without a known histological stage.
df = df.dropna(subset=[target_column]).copy()

# Keep only the four documented stage values.
df = df[df[target_column].isin([1, 2, 3, 4])].copy()

print("Dataset:", DATA_PATH)
print("Rows used:", len(df))
print("\nHistological stage distribution:")
print(df[target_column].value_counts().sort_index())


# --------------------------------------------------
# 3. Define the four model configurations
# --------------------------------------------------

def make_model(algorithm):
    """Create a fresh model pipeline for each fold."""

    if algorithm == "Logistic Regression":
        return Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            (
                "classifier",
                LogisticRegression(
                    max_iter=2000,
                    class_weight="balanced",
                    random_state=RANDOM_STATE,
                ),
            ),
        ])

    if algorithm == "Random Forest":
        return Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            (
                "classifier",
                RandomForestClassifier(
                    n_estimators=300,
                    max_depth=8,
                    min_samples_split=5,
                    min_samples_leaf=2,
                    class_weight="balanced",
                    random_state=RANDOM_STATE,
                    n_jobs=-1,
                ),
            ),
        ])

    raise ValueError(f"Unknown algorithm: {algorithm}")


configurations = [
    {
        "model": "A",
        "features": "Baseline",
        "algorithm": "Logistic Regression",
        "columns": BASELINE_FEATURES,
    },
    {
        "model": "B",
        "features": "Expanded",
        "algorithm": "Logistic Regression",
        "columns": EXPANDED_FEATURES,
    },
    {
        "model": "C",
        "features": "Baseline",
        "algorithm": "Random Forest",
        "columns": BASELINE_FEATURES,
    },
    {
        "model": "D",
        "features": "Expanded",
        "algorithm": "Random Forest",
        "columns": EXPANDED_FEATURES,
    },
]


# --------------------------------------------------
# 4. Define the two binary classification targets
# --------------------------------------------------

targets = {
    "Target A: Stage 1 vs Stages 2-4": (
        (df[target_column] >= 2).astype(int)
    ),
    "Target B: Stages 1-2 vs Stages 3-4": (
        (df[target_column] >= 3).astype(int)
    ),
}


# --------------------------------------------------
# 5. Run identical stratified cross-validation
# --------------------------------------------------

fold_results = []

for target_name, y_all in targets.items():

    print(f"\n{'=' * 65}")
    print(target_name)
    print("Class counts:")
    print(y_all.value_counts().sort_index().to_dict())

    # Reset indexes to align features and target.
    y_all = y_all.reset_index(drop=True)
    X_all = df[EXPANDED_FEATURES].reset_index(drop=True)

    cv = StratifiedKFold(
        n_splits=N_SPLITS,
        shuffle=True,
        random_state=RANDOM_STATE,
    )

    for config in configurations:

        X = X_all[config["columns"]]
        algorithm = config["algorithm"]

        for fold, (train_idx, test_idx) in enumerate(
            cv.split(X, y_all), start=1
        ):

            X_train = X.iloc[train_idx]
            X_test = X.iloc[test_idx]
            y_train = y_all.iloc[train_idx]
            y_test = y_all.iloc[test_idx]

            model = make_model(algorithm)
            model.fit(X_train, y_train)

            predictions = model.predict(X_test)
            probabilities = model.predict_proba(X_test)[:, 1]

            # For labels 0 and 1:
            # label 1 is the positive class.
            tn, fp, fn, tp = (
                __import__("sklearn.metrics", fromlist=["confusion_matrix"])
                .confusion_matrix(
                    y_test, predictions, labels=[0, 1]
                )
                .ravel()
            )

            specificity = (
                tn / (tn + fp)
                if (tn + fp) > 0 else 0.0
            )

            fold_results.append({
                "target": target_name,
                "model": config["model"],
                "features": config["features"],
                "algorithm": algorithm,
                "fold": fold,
                "accuracy": accuracy_score(
                    y_test, predictions
                ),
                "balanced_accuracy": balanced_accuracy_score(
                    y_test, predictions
                ),
                "precision": precision_score(
                    y_test, predictions, zero_division=0
                ),
                "sensitivity": recall_score(
                    y_test, predictions, zero_division=0
                ),
                "specificity": specificity,
                "f1": f1_score(
                    y_test, predictions, zero_division=0
                ),
                "roc_auc": roc_auc_score(
                    y_test, probabilities
                ),
            })

        print(
            f"Completed Model {config['model']} "
            f"({algorithm}, {config['features']} features)"
        )


# --------------------------------------------------
# 6. Summarize the results across folds
# --------------------------------------------------

fold_df = pd.DataFrame(fold_results)

metrics = [
    "accuracy",
    "balanced_accuracy",
    "precision",
    "sensitivity",
    "specificity",
    "f1",
    "roc_auc",
]

group_columns = [
    "target",
    "model",
    "features",
    "algorithm",
]

summary = (
    fold_df.groupby(group_columns)[metrics]
    .agg(["mean", "std"])
    .reset_index()
)

# Flatten the multi-level column names.
summary.columns = [
    "_".join(str(part) for part in column if part)
    if isinstance(column, tuple)
    else column
    for column in summary.columns
]

fold_path = OUTPUT_DIR / "experiment3_four_model_fold_results.csv"
summary_path = OUTPUT_DIR / "experiment3_four_model_summary.csv"
json_path = OUTPUT_DIR / "experiment3_four_model_summary.json"

fold_df.to_csv(fold_path, index=False)
summary.to_csv(summary_path, index=False)

with open(json_path, "w", encoding="utf-8") as file:
    json.dump(
        {
            "dataset": str(DATA_PATH),
            "rows_used": int(len(df)),
            "cross_validation": {
                "method": "StratifiedKFold",
                "folds": N_SPLITS,
                "shuffle": True,
                "random_state": RANDOM_STATE,
            },
            "positive_class": (
                "1: Stage 2-4 for Target A; "
                "Stage 3-4 for Target B"
            ),
            "results": summary.to_dict(orient="records"),
            "note": (
                "Exploratory internal validation only. "
                "AST 1 and ALT 1 are dataset-specific ratio "
                "variables and are not assumed to be standard "
                "clinical U/L measurements. Results do not "
                "establish clinical validity."
            ),
        },
        file,
        indent=2,
    )

print("\n" + "=" * 65)
print("FINAL CROSS-VALIDATION SUMMARY")
print("=" * 65)

display_columns = group_columns + [
    "balanced_accuracy_mean",
    "balanced_accuracy_std",
    "sensitivity_mean",
    "specificity_mean",
    "f1_mean",
    "roc_auc_mean",
    "roc_auc_std",
]

print(
    summary[display_columns].round(4).to_string(index=False)
)

print("\nFiles saved:")
print(f"Fold-level results: {fold_path}")
print(f"Summary CSV:        {summary_path}")
print(f"Summary JSON:       {json_path}")
