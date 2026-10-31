"""
SUGAR — Model 4: Disease Etiology & Clinical Stigmata Pipeline.

Dataset:
    Mayo Clinic Primary Biliary Cirrhosis (PBC) Study (data/cirrhosis.csv, N=418).
    Gold Standard: Histologically confirmed liver biopsy staging (Stage 1 to 4).

Target Definition:
    Primary Target (Advanced Fibrosis / Cirrhosis, Target B equivalent):
        Stage 1-2 -> 0 (Early/Moderate Fibrosis)
        Stage 3-4 -> 1 (Advanced Fibrosis / Cirrhosis)

Features:
    - Clinical Stigmata & Physical Signs: Ascites, Hepatomegaly, Spiders, Edema
    - Demographics: Age (years, converted from days), Sex
    - Laboratory Biomarkers: Bilirubin, Albumin, Platelets, SGOT (AST), Alk_Phos, Copper, Prothrombin

Evaluation Methodology:
    - Stratified 80/20 train/test holdout split (random_state=42)
    - 5-fold Stratified Cross-Validation on training split
    - Strict leakage prevention: all imputation, encoding, and scaling fitted within CV folds
    - Held-out test evaluation on the untouched 20% test partition
"""
from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
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
from sklearn.model_selection import StratifiedKFold, cross_validate, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "cirrhosis.csv"
MODEL_PATH = BASE_DIR / "models" / "etiology_stigmata_model.pkl"
METRICS_PATH = BASE_DIR / "outputs" / "model4_etiology_stigmata_metrics.json"

MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)

RANDOM_STATE = 42


def load_and_prepare_cirrhosis_data(data_path: Path) -> Tuple[pd.DataFrame, pd.Series]:
    df = pd.read_csv(data_path)
    # Filter to patients with confirmed histological stage
    df = df.dropna(subset=["Stage"]).copy()
    df["Stage"] = df["Stage"].astype(int)

    # Primary target: Advanced Fibrosis (Stage 3-4 vs Stage 1-2)
    df["advanced_fibrosis"] = (df["Stage"] >= 3).astype(int)

    # Convert Age from days to years
    df["Age_years"] = df["Age"] / 365.25

    return df


def get_model4_feature_lists():
    numeric_features = [
        "Age_years",
        "Bilirubin",
        "Albumin",
        "Platelets",
        "SGOT",
        "Alk_Phos",
        "Copper",
        "Prothrombin",
    ]
    categorical_features = [
        "Sex",
        "Ascites",
        "Hepatomegaly",
        "Spiders",
        "Edema",
    ]
    return numeric_features, categorical_features


def build_pipeline(classifier_type: str = "rf") -> Pipeline:
    numeric_features, categorical_features = get_model4_feature_lists()

    numeric_transformer = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])

    categorical_transformer = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
    ])

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, numeric_features),
            ("cat", categorical_transformer, categorical_features),
        ]
    )

    if classifier_type == "rf":
        clf = RandomForestClassifier(
            n_estimators=300,
            max_depth=6,
            min_samples_split=4,
            min_samples_leaf=2,
            class_weight="balanced",
            random_state=RANDOM_STATE,
        )
    else:
        clf = LogisticRegression(
            max_iter=1000,
            class_weight="balanced",
            random_state=RANDOM_STATE,
        )

    return Pipeline([
        ("preprocessor", preprocessor),
        ("classifier", clf),
    ])


def main():
    print("=" * 60)
    print("SUGAR — Model 4: Etiology & Clinical Stigmata Pipeline")
    print("=" * 60)

    df = load_and_prepare_cirrhosis_data(DATA_PATH)
    numeric_features, categorical_features = get_model4_feature_lists()
    all_features = numeric_features + categorical_features

    X = df[all_features].copy()
    y = df["advanced_fibrosis"]

    print(f"Cohort size: {len(df)} patients with confirmed histological stage.")
    print("Target distribution (Advanced Fibrosis: Stage 3-4):")
    print(y.value_counts(normalize=True).round(3))

    # Stratified Holdout Split (80% train, 20% test)
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        random_state=RANDOM_STATE,
        stratify=y,
    )
    print(f"\nTrain set: N={len(X_train)} (Positive: {y_train.sum()})")
    print(f"Held-out test set: N={len(X_test)} (Positive: {y_test.sum()})")

    # 5-Fold Stratified CV on Training Set
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
    cv_pipeline = build_pipeline("rf")

    scoring = {
        "accuracy": "accuracy",
        "balanced_accuracy": "balanced_accuracy",
        "precision": "precision",
        "recall": "recall",
        "f1": "f1",
        "roc_auc": "roc_auc",
    }

    cv_results = cross_validate(
        cv_pipeline,
        X_train,
        y_train,
        cv=cv,
        scoring=scoring,
        n_jobs=-1,
    )

    print("\n--- 5-Fold Cross-Validation Results (Training Split) ---")
    cv_summary = {}
    for metric in scoring:
        mean_score = float(cv_results[f"test_{metric}"].mean())
        std_score = float(cv_results[f"test_{metric}"].std())
        cv_summary[metric] = round(mean_score, 4)
        cv_summary[f"{metric}_std"] = round(std_score, 4)
        print(f"{metric.capitalize():18s}: {mean_score:.4f} (+/- {std_score:.4f})")

    # Fit final model on Training Split and evaluate on untouched Held-Out Test Set
    final_pipeline = build_pipeline("rf")
    final_pipeline.fit(X_train, y_train)

    y_pred = final_pipeline.predict(X_test)
    y_prob = final_pipeline.predict_proba(X_test)[:, 1]

    tn, fp, fn, tp = confusion_matrix(y_test, y_pred).ravel()
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0

    test_metrics = {
        "accuracy": round(float(accuracy_score(y_test, y_pred)), 4),
        "balanced_accuracy": round(float(balanced_accuracy_score(y_test, y_pred)), 4),
        "precision": round(float(precision_score(y_test, y_pred, zero_division=0)), 4),
        "recall": round(float(recall_score(y_test, y_pred, zero_division=0)), 4),
        "specificity": round(float(specificity), 4),
        "f1": round(float(f1_score(y_test, y_pred, zero_division=0)), 4),
        "roc_auc": round(float(roc_auc_score(y_test, y_prob)), 4),
        "confusion_matrix": {
            "tn": int(tn),
            "fp": int(fp),
            "fn": int(fn),
            "tp": int(tp),
        },
    }

    print("\n--- Held-Out Test Set Evaluation (N=83) ---")
    for k, v in test_metrics.items():
        if k != "confusion_matrix":
            print(f"{k.capitalize():18s}: {v}")
    print(f"Confusion Matrix: TN={tn}, FP={fp}, FN={fn}, TP={tp}")

    # Extract feature importances
    preprocessor = final_pipeline.named_steps["preprocessor"]
    cat_encoder = preprocessor.named_transformers_["cat"].named_steps["onehot"]
    cat_encoded_names = list(cat_encoder.get_feature_names_out(categorical_features))
    transformed_feature_names = numeric_features + cat_encoded_names

    rf_clf = final_pipeline.named_steps["classifier"]
    importances = dict(zip(transformed_feature_names, [round(float(x), 4) for x in rf_clf.feature_importances_]))
    sorted_importances = dict(sorted(importances.items(), key=lambda item: item[1], reverse=True))

    print("\n--- Top 10 Feature Importances ---")
    for feat, imp in list(sorted_importances.items())[:10]:
        print(f"{feat:25s}: {imp:.4f}")

    # Save artifact
    joblib.dump(final_pipeline, MODEL_PATH)
    print(f"\nTrained Model 4 artifact saved to: {MODEL_PATH}")

    # Save metrics JSON
    metrics_payload = {
        "model_name": "Model 4: Disease Etiology & Clinical Stigmata",
        "dataset": {
            "name": "Mayo Clinic Primary Biliary Cirrhosis (PBC) Trial",
            "source_file": "data/cirrhosis.csv",
            "total_rows": len(df),
            "train_rows": len(X_train),
            "test_rows": len(X_test),
        },
        "target": {
            "name": "advanced_fibrosis",
            "definition": "Histological Biopsy Stage 3-4 vs Stage 1-2",
            "prevalence": round(float(y.mean()), 4),
        },
        "features": {
            "numeric": numeric_features,
            "categorical": categorical_features,
            "all_features": all_features,
        },
        "cross_validation_5fold": cv_summary,
        "held_out_test_metrics": test_metrics,
        "feature_importances": sorted_importances,
        "scientific_disclaimer": (
            "Research-grade predictive model trained on biopsy-confirmed Primary Biliary Cirrhosis trial cohort. "
            "Evaluates clinical stigmata (ascites, hepatomegaly, spiders, edema) and laboratory biomarkers. "
            "Not for autonomous clinical diagnosis or treatment decisions."
        ),
    }

    with open(METRICS_PATH, "w", encoding="utf-8") as f:
        json.dump(metrics_payload, f, indent=2)
    print(f"Metrics saved to: {METRICS_PATH}")


if __name__ == "__main__":
    main()
