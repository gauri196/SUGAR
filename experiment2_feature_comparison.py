
from pathlib import Path
import json

import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import RepeatedStratifiedKFold, cross_validate

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "hcvdat0.csv"
OUTPUT_DIR = BASE_DIR / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

df = pd.read_csv(DATA_PATH)
df = df.drop(columns=["Unnamed: 0"], errors="ignore")
df = df.dropna(subset=["Category"]).copy()

y = df["Category"].astype(str)

# Compare feature groups using the same evaluation splits.
feature_groups = {
    "Demographics_only": ["Age", "Sex"],
    "Basic_liver_markers": ["Age", "Sex", "ALT", "AST", "ALB", "BIL"],
    "Expanded_liver_markers": [
        "Age", "Sex", "ALT", "AST", "ALB", "BIL",
        "ALP", "GGT", "PROT", "CHE", "CHOL", "CREA"
    ],
}

# Smallest class has only 7 records. Five folds repeated twice
# keeps each validation fold small but includes rare categories.
cv = RepeatedStratifiedKFold(
    n_splits=5,
    n_repeats=2,
    random_state=42,
)

results = []

for group_name, features in feature_groups.items():
    X = df[features].copy()

    numeric_features = X.select_dtypes(
        include=["number"]
    ).columns.tolist()
    categorical_features = X.select_dtypes(
        include=["object", "str", "category", "bool"]
    ).columns.tolist()

    transformers = []

    if numeric_features:
        transformers.append((
            "numeric",
            SimpleImputer(strategy="median"),
            numeric_features,
        ))

    if categorical_features:
        categorical_pipeline = Pipeline([
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ])
        transformers.append((
            "categorical",
            categorical_pipeline,
            categorical_features,
        ))

    preprocessor = ColumnTransformer(transformers)

    model = Pipeline([
        ("preprocessor", preprocessor),
        ("classifier", RandomForestClassifier(
            n_estimators=300,
            class_weight="balanced_subsample",
            min_samples_leaf=2,
            random_state=42,
        )),
    ])

    scores = cross_validate(
        model,
        X,
        y,
        cv=cv,
        scoring={
            "accuracy": "accuracy",
            "balanced_accuracy": "balanced_accuracy",
            "macro_f1": "f1_macro",
        },
        return_train_score=False,
        error_score="raise",
    )

    result = {
        "feature_group": group_name,
        "features": features,
        "accuracy_mean": float(np.mean(scores["test_accuracy"])),
        "accuracy_std": float(np.std(scores["test_accuracy"])),
        "balanced_accuracy_mean": float(
            np.mean(scores["test_balanced_accuracy"])
        ),
        "balanced_accuracy_std": float(
            np.std(scores["test_balanced_accuracy"])
        ),
        "macro_f1_mean": float(np.mean(scores["test_macro_f1"])),
        "macro_f1_std": float(np.std(scores["test_macro_f1"])),
    }

    results.append(result)

    print(f"\n=== {group_name} ===")
    print("Features:", ", ".join(features))
    print(
        f"Accuracy: {result['accuracy_mean']:.3f} "
        f"+/- {result['accuracy_std']:.3f}"
    )
    print(
        f"Balanced accuracy: {result['balanced_accuracy_mean']:.3f} "
        f"+/- {result['balanced_accuracy_std']:.3f}"
    )
    print(
        f"Macro F1: {result['macro_f1_mean']:.3f} "
        f"+/- {result['macro_f1_std']:.3f}"
    )

output_path = OUTPUT_DIR / "uci_hcv_feature_comparison.json"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)

print("\n=== Comparison summary ===")
summary = pd.DataFrame(results)[[
    "feature_group",
    "accuracy_mean",
    "balanced_accuracy_mean",
    "macro_f1_mean",
]]
print(summary.to_string(index=False))

print("\nSaved comparison:", output_path)
print(
    "\nResearch note: repeated cross-validation scores are exploratory. "
    "The rare classes contain very few records, so estimates may be unstable."
)
