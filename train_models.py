import pandas as pd
import numpy as np
import joblib
import json

from sklearn.model_selection import (
    StratifiedKFold,
    cross_validate,
    train_test_split
)
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    make_scorer
)


# ============================================================
# 1. SETTINGS
# ============================================================

DATA_PATH = "data/HCV-Egy-Data.csv"

BASELINE_MODEL_PATH = "models/routine_clinical_baseline.pkl"
EXPANDED_MODEL_PATH = "models/expanded_fibrosis_model.pkl"
METRICS_PATH = "models/metrics.json"

RANDOM_STATE = 42
''

# ============================================================
# 2. LOAD DATA
# ============================================================

print("\n========================================")
print("LIVER FIBROSIS MODEL TRAINING")
print("========================================")

df = pd.read_csv(DATA_PATH)

# Remove extra spaces from column names
df.columns = df.columns.str.strip()

print("\nDataset loaded successfully")
print("Shape:", df.shape)


# ============================================================
# 3. CHECK REQUIRED COLUMNS
# ============================================================

required_columns = [
    "Age",
    "BMI",
    "Plat",
    "AST 1",
    "ALT 1",
    "WBC",
    "RBC",
    "HGB",
    "Baselinehistological staging"
]

missing_columns = [
    col for col in required_columns
    if col not in df.columns
]

if missing_columns:
    print("\nERROR: Missing columns:")
    print(missing_columns)
    raise ValueError(
        "Required columns are missing from the dataset."
    )


# ============================================================
# 4. CONVERT VARIABLES TO NUMERIC
# ============================================================

for col in required_columns:

    df[col] = pd.to_numeric(
        df[col],
        errors="coerce"
    )


# ============================================================
# 5. REMOVE ROWS WITHOUT TARGET
# ============================================================

df = df.dropna(
    subset=["Baselinehistological staging"]
).copy()


# ============================================================
# 6. CREATE TARGET 1
# ============================================================
#
# Target 1:
#
# Stage 1     -> 0
# Stage 2-4   -> 1
#
# This represents:
# No significant fibrosis vs significant fibrosis
#
# ============================================================

df["significant_fibrosis"] = (
    df["Baselinehistological staging"] >= 2
).astype(int)


print("\nTarget 1: Significant Fibrosis")
print("----------------------------------------")
print(
    df["significant_fibrosis"]
    .value_counts()
    .sort_index()
)


# ============================================================
# 7. CREATE TARGET 2
# ============================================================
#
# Target 2:
#
# Stage 1-2 -> 0
# Stage 3-4 -> 1
#
# This represents:
# Lower fibrosis vs advanced fibrosis
#
# ============================================================

df["advanced_fibrosis"] = (
    df["Baselinehistological staging"] >= 3
).astype(int)


print("\nTarget 2: Advanced Fibrosis")
print("----------------------------------------")
print(
    df["advanced_fibrosis"]
    .value_counts()
    .sort_index()
)


# ============================================================
# 8. DEFINE FEATURES
# ============================================================

baseline_features = [
    "Age",
    "BMI",
    "Plat",
    "AST 1",
    "ALT 1"
]

expanded_features = [
    "Age",
    "BMI",
    "Plat",
    "AST 1",
    "ALT 1",
    "WBC",
    "RBC",
    "HGB"
]


print("\nBaseline features:")
print(baseline_features)

print("\nExpanded features:")
print(expanded_features)


# ============================================================
# 9. MODEL DEFINITIONS
# ============================================================

baseline_model = Pipeline([
    (
        "imputer",
        SimpleImputer(strategy="median")
    ),

    (
        "scaler",
        StandardScaler()
    ),

    (
        "model",
        LogisticRegression(
            max_iter=2000,
            class_weight="balanced",
            random_state=RANDOM_STATE
        )
    )
])


expanded_model = Pipeline([
    (
        "imputer",
        SimpleImputer(strategy="median")
    ),

    (
        "model",
        RandomForestClassifier(
            n_estimators=300,
            max_depth=8,
            min_samples_split=5,
            min_samples_leaf=2,
            class_weight="balanced",
            random_state=RANDOM_STATE,
            n_jobs=-1
        )
    )
])


# ============================================================
# 10. CROSS-VALIDATION SCORING
# ============================================================

def specificity_score(y_true, y_pred):

    tn, fp, fn, tp = confusion_matrix(
        y_true,
        y_pred,
        labels=[0, 1]
    ).ravel()

    if (tn + fp) == 0:
        return 0.0

    return tn / (tn + fp)


scoring = {
    "accuracy": "accuracy",

    "precision": make_scorer(
        precision_score,
        zero_division=0
    ),

    "recall": make_scorer(
        recall_score,
        zero_division=0
    ),

    "specificity": make_scorer(
        specificity_score
    ),

    "f1": make_scorer(
        f1_score,
        zero_division=0
    ),

    "roc_auc": "roc_auc"
}


# ============================================================
# 11. CROSS-VALIDATION FUNCTION
# ============================================================

def run_cross_validation(
    model,
    X,
    y,
    model_name
):

    print("\n========================================")
    print(model_name)
    print("========================================")

    cv = StratifiedKFold(
        n_splits=10,
        shuffle=True,
        random_state=RANDOM_STATE
    )

    results = cross_validate(
        model,
        X,
        y,
        cv=cv,
        scoring=scoring,
        n_jobs=-1
    )

    output = {
        "model": model_name
    }

    for metric in scoring.keys():

        scores = results[
            "test_" + metric
        ]

        mean_score = scores.mean()
        std_score = scores.std()

        output[metric] = round(
            float(mean_score),
            4
        )

        output[metric + "_std"] = round(
            float(std_score),
            4
        )

        print(
            f"{metric.capitalize():12s}: "
            f"{mean_score:.4f} "
            f"(± {std_score:.4f})"
        )

    return output


# ============================================================
# 12. RUN EXPERIMENT
# ============================================================

# ------------------------------------------------------------
# Experiment A
# Significant fibrosis
# Stage 1 vs Stage 2-4
# ------------------------------------------------------------

print("\n\n########################################")
print("EXPERIMENT A")
print("Stage 1 vs Stage 2-4")
print("########################################")


X_baseline_A = df[baseline_features]
X_expanded_A = df[expanded_features]

y_A = df["significant_fibrosis"]


baseline_A_results = run_cross_validation(
    baseline_model,
    X_baseline_A,
    y_A,
    "Routine Clinical Baseline - Target A"
)


expanded_A_results = run_cross_validation(
    expanded_model,
    X_expanded_A,
    y_A,
    "Expanded Random Forest - Target A"
)


# ============================================================
# 13. EXPERIMENT B
# ============================================================

print("\n\n########################################")
print("EXPERIMENT B")
print("Stage 1-2 vs Stage 3-4")
print("########################################")


X_baseline_B = df[baseline_features]
X_expanded_B = df[expanded_features]

y_B = df["advanced_fibrosis"]


baseline_B_results = run_cross_validation(
    baseline_model,
    X_baseline_B,
    y_B,
    "Routine Clinical Baseline - Target B"
)


expanded_B_results = run_cross_validation(
    expanded_model,
    X_expanded_B,
    y_B,
    "Expanded Random Forest - Target B"
)


# ============================================================
# 14. TRAIN FINAL MODELS
# ============================================================
#
# For the application prototype we will train on the complete
# dataset using Target B:
#
# Stage 1-2 -> 0
# Stage 3-4 -> 1
#
# ============================================================

print("\n\n========================================")
print("TRAINING FINAL APPLICATION MODELS")
print("========================================")


final_baseline_model = Pipeline([
    (
        "imputer",
        SimpleImputer(strategy="median")
    ),

    (
        "scaler",
        StandardScaler()
    ),

    (
        "model",
        LogisticRegression(
            max_iter=2000,
            class_weight="balanced",
            random_state=RANDOM_STATE
        )
    )
])


final_expanded_model = Pipeline([
    (
        "imputer",
        SimpleImputer(strategy="median")
    ),

    (
        "model",
        RandomForestClassifier(
            n_estimators=300,
            max_depth=8,
            min_samples_split=5,
            min_samples_leaf=2,
            class_weight="balanced",
            random_state=RANDOM_STATE,
            n_jobs=-1
        )
    )
])


# Train on all available data

final_baseline_model.fit(
    X_baseline_B,
    y_B
)

final_expanded_model.fit(
    X_expanded_B,
    y_B
)


# ============================================================
# 15. SAVE MODELS
# ============================================================

joblib.dump(
    final_baseline_model,
    BASELINE_MODEL_PATH
)

joblib.dump(
    final_expanded_model,
    EXPANDED_MODEL_PATH
)


print("\nModels saved:")
print(BASELINE_MODEL_PATH)
print(EXPANDED_MODEL_PATH)


# ============================================================
# 16. RANDOM FOREST FEATURE IMPORTANCE
# ============================================================

rf_model = (
    final_expanded_model
    .named_steps["model"]
)

feature_importance = dict(
    zip(
        expanded_features,
        rf_model.feature_importances_
    )
)


# Sort feature importance

feature_importance = dict(
    sorted(
        feature_importance.items(),
        key=lambda x: x[1],
        reverse=True
    )
)


print("\n========================================")
print("RANDOM FOREST FEATURE IMPORTANCE")
print("========================================")

for feature, importance in feature_importance.items():

    print(
        f"{feature:10s}: "
        f"{importance:.4f}"
    )


# ============================================================
# 17. SAVE METRICS
# ============================================================

metrics = {

    "dataset": {
        "name": "UCI Hepatitis C Virus (HCV) for Egyptian Patients",
        "rows": int(len(df)),
        "columns": int(len(df.columns))
    },

    "note": (
        "AST 1 and ALT 1 are dataset-specific ratio variables. "
        "They are not treated as standard U/L AST and ALT values "
        "for a clinical FIB-4 calculation."
    ),

    "target_A": {
        "definition": "Stage 1 vs Stage 2-4",
        "baseline": baseline_A_results,
        "expanded": expanded_A_results
    },

    "target_B": {
        "definition": "Stage 1-2 vs Stage 3-4",
        "baseline": baseline_B_results,
        "expanded": expanded_B_results
    },

    "features": {
        "baseline": baseline_features,
        "expanded": expanded_features
    },

    "feature_importance": feature_importance
}


with open(
    METRICS_PATH,
    "w"
) as file:

    json.dump(
        metrics,
        file,
        indent=4
    )


# ============================================================
# 18. FINAL MESSAGE
# ============================================================

print("\n========================================")
print("TRAINING COMPLETE")
print("========================================")

print("\nCreated files:")

print(
    f"✓ {BASELINE_MODEL_PATH}"
)

print(
    f"✓ {EXPANDED_MODEL_PATH}"
)

print(
    f"✓ {METRICS_PATH}"
)

print("\nThe models are ready for the application prototype.")