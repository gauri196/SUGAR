
from pathlib import Path
import json

import pandas as pd
import joblib

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    f1_score,
    classification_report,
    confusion_matrix,
)

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "hcvdat0.csv"
MODEL_DIR = BASE_DIR / "models"
OUTPUT_DIR = BASE_DIR / "outputs"

MODEL_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# 1. Load and validate data
df = pd.read_csv(DATA_PATH)

# The index column is not a clinical feature.
df = df.drop(columns=["Unnamed: 0"], errors="ignore")

target = "Category"
df = df.dropna(subset=[target]).copy()

X = df.drop(columns=[target])
y = df[target].astype(str)

numeric_features = X.select_dtypes(include=["number"]).columns.tolist()
categorical_features = X.select_dtypes(
    include=["object", "str", "category", "bool"]
).columns.tolist()
# 2. Preprocess features inside the pipeline.
# Imputers are fitted only on training data.
numeric_pipeline = Pipeline([
    ("imputer", SimpleImputer(strategy="median")),
])

categorical_pipeline = Pipeline([
    ("imputer", SimpleImputer(strategy="most_frequent")),
    ("onehot", OneHotEncoder(handle_unknown="ignore")),
])

preprocessor = ColumnTransformer([
    ("numeric", numeric_pipeline, numeric_features),
    ("categorical", categorical_pipeline, categorical_features),
])

# 3. Build an exploratory five-class classifier.
model = Pipeline([
    ("preprocessor", preprocessor),
    ("classifier", RandomForestClassifier(
        n_estimators=300,
        class_weight="balanced_subsample",
        random_state=42,
        min_samples_leaf=2,
    )),
])

# 4. Stratified holdout split
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y,
)

print("Training rows:", len(X_train))
print("Testing rows:", len(X_test))
print("\nTraining class counts:")
print(y_train.value_counts())
print("\nTesting class counts:")
print(y_test.value_counts())

# 5. Train and evaluate
model.fit(X_train, y_train)
predictions = model.predict(X_test)

labels = sorted(y.unique())

accuracy = accuracy_score(y_test, predictions)
balanced_accuracy = balanced_accuracy_score(y_test, predictions)
macro_f1 = f1_score(
    y_test, predictions, average="macro", zero_division=0
)

print("\n=== UCI HCV Exploratory Results ===")
print(f"Accuracy:          {accuracy:.4f}")
print(f"Balanced accuracy: {balanced_accuracy:.4f}")
print(f"Macro F1:          {macro_f1:.4f}")

print("\n=== Per-class report ===")
report = classification_report(
    y_test,
    predictions,
    labels=labels,
    output_dict=True,
    zero_division=0,
)
print(classification_report(
    y_test,
    predictions,
    labels=labels,
    zero_division=0,
))

print("=== Confusion matrix ===")
matrix = confusion_matrix(y_test, predictions, labels=labels)
print("Label order:", labels)
print(matrix)

# 6. Save the model and results separately from Experiment 1.
model_path = MODEL_DIR / "uci_hcv_exploratory_model.pkl"
metrics_path = OUTPUT_DIR / "uci_hcv_experiment2_metrics.json"

joblib.dump(model, model_path)

metrics = {
    "experiment": "UCI HCV five-class exploratory classification",
    "dataset_rows": int(len(df)),
    "feature_columns": X.columns.tolist(),
    "target": target,
    "class_counts": {
        str(k): int(v) for k, v in y.value_counts().items()
    },
    "test_accuracy": float(accuracy),
    "test_balanced_accuracy": float(balanced_accuracy),
    "test_macro_f1": float(macro_f1),
    "classification_report": report,
    "confusion_matrix_labels": labels,
    "confusion_matrix": matrix.tolist(),
    "limitations": [
        "Small and imbalanced diagnostic categories",
        "Single stratified holdout evaluation",
        "Exploratory results, not clinical validation",
    ],
}

with open(metrics_path, "w", encoding="utf-8") as f:
    json.dump(metrics, f, indent=2)

print("\nSaved model:", model_path)
print("Saved metrics:", metrics_path)
print("\nThis is a research experiment, not a diagnostic tool.")
