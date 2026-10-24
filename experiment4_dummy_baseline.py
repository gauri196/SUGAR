
from pathlib import Path

import pandas as pd

from sklearn.base import clone
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


# --------------------------------------------------
# 1. Configuration
# --------------------------------------------------

DATA_PATH = Path("data/HCV-Egy-Data.csv")
OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

RANDOM_STATE = 42
N_SPLITS = 10

BASELINE_FEATURES = [
    "Age", "BMI", "Plat", "AST 1", "ALT 1"
]

EXPANDED_FEATURES = BASELINE_FEATURES + [
    "WBC", "RBC", "HGB"
]


# --------------------------------------------------
# 2. Load dataset
# --------------------------------------------------

df = pd.read_csv(DATA_PATH)
df.columns = df.columns.str.strip()

target_column = "Baselinehistological staging"

required_columns = [target_column] + EXPANDED_FEATURES
missing = [c for c in required_columns if c not in df.columns]

if missing:
    raise ValueError(f"Missing required columns: {missing}")

for column in required_columns:
    df[column] = pd.to_numeric(df[column], errors="coerce")

df = df.dropna(subset=[target_column]).copy()
df = df[df[target_column].isin([1, 2, 3, 4])].reset_index(drop=True)

X_all = df[EXPANDED_FEATURES]

targets = {
    "Target A: Stage 1 vs Stages 2-4":
        (df[target_column] >= 2).astype(int),
    "Target B: Stages 1-2 vs Stages 3-4":
        (df[target_column] >= 3).astype(int),
}


# --------------------------------------------------
# 3. Define the four models
# --------------------------------------------------

def make_model(algorithm):
    if algorithm == "Logistic Regression":
        return Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            ("classifier", LogisticRegression(
                max_iter=2000,
                class_weight="balanced",
                random_state=RANDOM_STATE,
            )),
        ])

    if algorithm == "Random Forest":
        return Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("classifier", RandomForestClassifier(
                n_estimators=300,
                max_depth=8,
                min_samples_split=5,
                min_samples_leaf=2,
                class_weight="balanced",
                random_state=RANDOM_STATE,
                n_jobs=-1,
            )),
        ])

    raise ValueError(f"Unknown algorithm: {algorithm}")


models = [
    {
        "name": "A - Logistic Regression, baseline",
        "algorithm": "Logistic Regression",
        "features": BASELINE_FEATURES,
    },
    {
        "name": "B - Logistic Regression, expanded",
        "algorithm": "Logistic Regression",
        "features": EXPANDED_FEATURES,
    },
    {
        "name": "C - Random Forest, baseline",
        "algorithm": "Random Forest",
        "features": BASELINE_FEATURES,
    },
    {
        "name": "D - Random Forest, expanded",
        "algorithm": "Random Forest",
        "features": EXPANDED_FEATURES,
    },
]


# --------------------------------------------------
# 4. Cross-validation and majority-class benchmark
# --------------------------------------------------

summary_rows = []
confusion_rows = []

for target_name, y in targets.items():
    y = y.reset_index(drop=True)

    cv = StratifiedKFold(
        n_splits=N_SPLITS,
        shuffle=True,
        random_state=RANDOM_STATE,
    )

    X = X_all.reset_index(drop=True)

    # Dummy benchmark: always predicts the training fold's
    # most frequent class. No clinical features are used.
    all_models = [{
        "name": "Dummy - Most Frequent",
        "algorithm": "Dummy",
        "features": BASELINE_FEATURES,
    }] + models

    print(f"\n{'=' * 65}")
    print(target_name)
    print("Class counts:", y.value_counts().sort_index().to_dict())

    for config in all_models:
        selected_X = X[config["features"]]

        if config["algorithm"] == "Dummy":
            estimator = DummyClassifier(strategy="most_frequent")
        else:
            estimator = make_model(config["algorithm"])

        # Each row receives an out-of-fold prediction:
        # it is predicted by a model that did not train on it.
        predictions = cross_val_predict(
            clone(estimator),
            selected_X,
            y,
            cv=cv,
            method="predict",
            n_jobs=1,
        )

        probabilities = cross_val_predict(
            clone(estimator),
            selected_X,
            y,
            cv=cv,
            method="predict_proba",
            n_jobs=1,
        )[:, 1]

        tn, fp, fn, tp = confusion_matrix(
            y, predictions, labels=[0, 1]
        ).ravel()

        sensitivity = tp / (tp + fn) if (tp + fn) else 0.0
        specificity = tn / (tn + fp) if (tn + fp) else 0.0

        summary_rows.append({
            "target": target_name,
            "model": config["name"],
            "accuracy": accuracy_score(y, predictions),
            "balanced_accuracy": balanced_accuracy_score(
                y, predictions
            ),
            "precision": precision_score(
                y, predictions, zero_division=0
            ),
            "sensitivity": sensitivity,
            "specificity": specificity,
            "f1": f1_score(y, predictions, zero_division=0),
            "roc_auc": roc_auc_score(y, probabilities),
        })

        confusion_rows.append({
            "target": target_name,
            "model": config["name"],
            "TN": int(tn),
            "FP": int(fp),
            "FN": int(fn),
            "TP": int(tp),
        })

        print(f"Completed: {config['name']}")


# --------------------------------------------------
# 5. Save results
# --------------------------------------------------

summary = pd.DataFrame(summary_rows)
confusions = pd.DataFrame(confusion_rows)

summary_path = OUTPUT_DIR / "experiment4_dummy_summary.csv"
confusion_path = OUTPUT_DIR / "experiment4_confusion_matrices.csv"

summary.to_csv(summary_path, index=False)
confusions.to_csv(confusion_path, index=False)

print("\n" + "=" * 65)
print("CROSS-VALIDATION RESULTS")
print("=" * 65)
print(summary.round(4).to_string(index=False))

print("\n" + "=" * 65)
print("CONFUSION MATRICES")
print("=" * 65)
print(confusions.to_string(index=False))

print("\nSaved files:")
print(summary_path)
print(confusion_path)

print(
    "\nNote: These are internal cross-validation results, "
    "not external or clinical validation."
)
