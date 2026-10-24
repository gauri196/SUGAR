
from pathlib import Path

import pandas as pd
import numpy as np

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import RepeatedStratifiedKFold
from sklearn.metrics import classification_report

BASE_DIR = Path(__file__).resolve().parent
df = pd.read_csv(BASE_DIR / "data" / "hcvdat0.csv")
df = df.drop(columns=["Unnamed: 0"], errors="ignore")
df = df.dropna(subset=["Category"]).copy()

features = [
    "Age", "Sex", "ALT", "AST", "ALB", "BIL",
    "ALP", "GGT", "PROT", "CHE", "CHOL", "CREA"
]
X = df[features]
y = df["Category"].astype(str)
labels = sorted(y.unique())

numeric = X.select_dtypes(include=["number"]).columns.tolist()
categorical = X.select_dtypes(
    include=["object", "str", "category", "bool"]
).columns.tolist()

preprocessor = ColumnTransformer([
    ("num", SimpleImputer(strategy="median"), numeric),
    ("cat", Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore")),
    ]), categorical),
])

model = Pipeline([
    ("preprocessor", preprocessor),
    ("classifier", RandomForestClassifier(
        n_estimators=300,
        class_weight="balanced_subsample",
        min_samples_leaf=2,
        random_state=42,
    )),
])

cv = RepeatedStratifiedKFold(
    n_splits=5,
    n_repeats=2,
    random_state=42,
)

# Collect out-of-fold predictions so every prediction is made
# by a model that did not train on that record.
all_true = []
all_pred = []

for train_idx, test_idx in cv.split(X, y):
    model.fit(X.iloc[train_idx], y.iloc[train_idx])
    pred = model.predict(X.iloc[test_idx])
    all_true.extend(y.iloc[test_idx].tolist())
    all_pred.extend(pred.tolist())

print("=== Pooled out-of-fold class report ===")
print(classification_report(
    all_true,
    all_pred,
    labels=labels,
    zero_division=0,
))

print("\n=== Per-class recall across pooled predictions ===")
report = classification_report(
    all_true,
    all_pred,
    labels=labels,
    output_dict=True,
    zero_division=0,
)
for label in labels:
    print(
        f"{label}: recall={report[label]['recall']:.3f}, "
        f"F1={report[label]['f1-score']:.3f}, "
        f"support={report[label]['support']}"
    )

print(
    "\nNote: each patient appears in a test fold once per repeat. "
    "Pooled predictions are repeated observations, not independent patients."
)
