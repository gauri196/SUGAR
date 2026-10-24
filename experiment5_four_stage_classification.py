
from pathlib import Path
import json

import numpy as np
import pandas as pd

from sklearn.dummy import DummyClassifier
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    roc_auc_score,
)

# --------------------------------------------------
# 1. PATHS AND CONFIGURATION
# --------------------------------------------------

DATA_PATH = Path("data/HCV-Egy-Data.csv")
OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

RANDOM_STATE = 42
N_SPLITS = 10
STAGE_COLUMN = "Baselinehistological staging"

# Features measured at baseline only.
BASELINE_FEATURES = [
    "Age",
    "BMI",
    "Plat",
    "AST 1",
    "ALT 1",
]

# Additional baseline blood measurements.
EXPANDED_FEATURES = BASELINE_FEATURES + [
    "WBC",
    "RBC",
    "HGB",
]

STAGES = [1, 2, 3, 4]


# --------------------------------------------------
# 2. LOAD AND PREPARE DATA
# --------------------------------------------------

if not DATA_PATH.exists():
    raise FileNotFoundError(
        f"Dataset not found: {DATA_PATH}\n"
        "Run this script from your SUGAR - Liver fibrosis folder."
    )

df = pd.read_csv(DATA_PATH)
df.columns = df.columns.str.strip()

required_columns = list(
    dict.fromkeys(
        [STAGE_COLUMN] + EXPANDED_FEATURES
    )
)

missing_columns = [
    col for col in required_columns if col not in df.columns
]

if missing_columns:
    raise ValueError(
        f"Missing required columns: {missing_columns}"
    )

for col in required_columns:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# Remove records without a known staging label.
df = df.dropna(subset=[STAGE_COLUMN]).copy()

# Keep only the four expected stages.
df = df[df[STAGE_COLUMN].isin(STAGES)].copy()
y = df[STAGE_COLUMN].astype(int)

print("=" * 65)
print("EXPERIMENT 5: FOUR-STAGE CLASSIFICATION")
print("=" * 65)

print(f"Dataset rows used: {len(df)}")
print("\nStage distribution:")
print(y.value_counts().sort_index().to_string())

print("\nImportant:")
print("- Grading is NOT used as a predictor.")
print("- Post-baseline ALT/RNA measurements are excluded.")
print("- Missing feature values are imputed inside each CV fold.")
print("- Results are exploratory, not clinical validation.")


# --------------------------------------------------
# 3. DEFINE MODELS
# --------------------------------------------------

def make_logistic_regression():
    return Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
        (
            "model",
            LogisticRegression(
                max_iter=3000,
                class_weight="balanced",
                random_state=RANDOM_STATE,
            ),
        ),
    ])


def make_random_forest():
    return Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        (
            "model",
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


models = {
    "Dummy - Most Frequent": {
        "features": BASELINE_FEATURES,
        "factory": lambda: DummyClassifier(
            strategy="most_frequent"
        ),
    },
    "A - Logistic Regression, baseline": {
        "features": BASELINE_FEATURES,
        "factory": make_logistic_regression,
    },
    "B - Logistic Regression, expanded": {
        "features": EXPANDED_FEATURES,
        "factory": make_logistic_regression,
    },
    "C - Random Forest, baseline": {
        "features": BASELINE_FEATURES,
        "factory": make_random_forest,
    },
    "D - Random Forest, expanded": {
        "features": EXPANDED_FEATURES,
        "factory": make_random_forest,
    },
}


# --------------------------------------------------
# 4. STRATIFIED CROSS-VALIDATION
# --------------------------------------------------

class_counts = y.value_counts()

if class_counts.min() < N_SPLITS:
    raise ValueError(
        f"At least {N_SPLITS} examples per stage are required "
        "for this cross-validation setup."
    )

cv = StratifiedKFold(
    n_splits=N_SPLITS,
    shuffle=True,
    random_state=RANDOM_STATE,
)

summary_rows = []
confusion_rows = []

for model_name, config in models.items():
    print("\n" + "-" * 65)
    print(f"Running: {model_name}")

    features = config["features"]
    X = df[features]

    model = config["factory"]()

    # Every row receives a prediction from a fold
    # in which that row was not used for training.
    predictions = cross_val_predict(
        model,
        X,
        y,
        cv=cv,
        method="predict",
        n_jobs=1,
    )

    probabilities = cross_val_predict(
        model,
        X,
        y,
        cv=cv,
        method="predict_proba",
        n_jobs=1,
    )

    # Cross-validation uses the same sorted class order
    # across folds. Verify it before calculating multiclass AUC.
    if hasattr(model, "classes_"):
        probability_classes = model.classes_
    else:
        probability_classes = np.unique(y)

    # Use the fitted model's class ordering when available
    # by verifying the order on a separate fit.
    model.fit(X, y)
    probability_classes = model.classes_

    class_order = list(probability_classes)
    if class_order != STAGES:
        raise ValueError(
            f"Unexpected probability class order: {class_order}"
        )

    accuracy = accuracy_score(y, predictions)
    balanced_accuracy = balanced_accuracy_score(y, predictions)
    macro_precision = precision_score(
        y, predictions, average="macro", zero_division=0
    )
    macro_recall = recall_score(
        y, predictions, average="macro", zero_division=0
    )
    macro_f1 = f1_score(
        y, predictions, average="macro", zero_division=0
    )

    try:
        macro_auc = roc_auc_score(
            y,
            probabilities,
            labels=STAGES,
            multi_class="ovr",
            average="macro",
        )
    except ValueError:
        macro_auc = np.nan

    summary_rows.append({
        "model": model_name,
        "features": len(features),
        "accuracy": accuracy,
        "balanced_accuracy": balanced_accuracy,
        "macro_precision": macro_precision,
        "macro_recall": macro_recall,
        "macro_f1": macro_f1,
        "macro_roc_auc_ovr": macro_auc,
    })

    cm = confusion_matrix(
        y,
        predictions,
        labels=STAGES,
    )

    for i, actual_stage in enumerate(STAGES):
        for j, predicted_stage in enumerate(STAGES):
            confusion_rows.append({
                "model": model_name,
                "actual_stage": actual_stage,
                "predicted_stage": predicted_stage,
                "count": int(cm[i, j]),
            })

    print(f"Accuracy:          {accuracy:.4f}")
    print(f"Balanced accuracy: {balanced_accuracy:.4f}")
    print(f"Macro precision:   {macro_precision:.4f}")
    print(f"Macro recall:      {macro_recall:.4f}")
    print(f"Macro F1:          {macro_f1:.4f}")
    print(f"Macro ROC-AUC:     {macro_auc:.4f}")

    print("\nConfusion matrix")
    print("Rows = actual stage; columns = predicted stage")
    print(pd.DataFrame(
        cm,
        index=[f"Actual {s}" for s in STAGES],
        columns=[f"Predicted {s}" for s in STAGES],
    ).to_string())


# --------------------------------------------------
# 5. SAVE RESULTS
# --------------------------------------------------

summary = pd.DataFrame(summary_rows).sort_values(
    "macro_f1",
    ascending=False,
)

confusion_df = pd.DataFrame(confusion_rows)

summary_path = OUTPUT_DIR / "experiment5_four_stage_summary.csv"
confusion_path = OUTPUT_DIR / "experiment5_four_stage_confusion_matrices.csv"
json_path = OUTPUT_DIR / "experiment5_four_stage_summary.json"

summary.to_csv(summary_path, index=False)
confusion_df.to_csv(confusion_path, index=False)

with open(json_path, "w", encoding="utf-8") as file:
    json.dump(
        summary.to_dict(orient="records"),
        file,
        indent=2,
        allow_nan=True,
    )

print("\n" + "=" * 65)
print("FINAL MODEL COMPARISON")
print("=" * 65)
print(summary.round(4).to_string(index=False))

print("\nFiles saved:")
print(summary_path)
print(confusion_path)
print(json_path)

print("\nExperiment 5 completed.")
