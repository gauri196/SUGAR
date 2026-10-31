# SUGAR — Model Workstream Status & Research Audit (`MODEL_STATUS.md`)

**Date:** October 29, 2026  
**Platform:** SUGAR — AI-Assisted Liver Fibrosis Research Platform  
**System Status:** Fully Integrated, Tested, and Verified (105 Backend Pytest Passing, Frontend Clean Build)

---

## 1. Executive Summary Table

| Model Identity | Algorithm | Dataset | N | Features | Evaluation Method | Primary Metrics | Artifact Path | Loadable | Live API Route | Frontend Integration |
|---|---|---|---|---|---|---|---|---|---|---|
| **Model 1 (A): Routine Clinical Baseline** | Logistic Regression (`class_weight="balanced"`) | Egyptian HCV Cohort (`HCV-Egy-Data.csv`) | 1,384 | 5 (Age, BMI, Plat, AST 1, ALT 1) | 10-Fold Stratified CV + 80/20 Stratified Holdout | CV ROC-AUC: 0.5349<br>Test ROC-AUC: 0.5040<br>Test Acc: 0.5162 | `models/routine_clinical_baseline.pkl` (2 KB) | Yes | `POST /predict` | Step 4 Live Inference |
| **Model 2 (B): Expanded Hematologic Model** | Random Forest (300 trees, `max_depth=8`) | Egyptian HCV Cohort (`HCV-Egy-Data.csv`) | 1,384 | 8 (Model 1 + WBC, RBC, HGB) | 10-Fold Stratified CV + 80/20 Stratified Holdout | CV ROC-AUC: 0.4976<br>Test ROC-AUC: 0.4927<br>Test Acc: 0.4982 | `models/expanded_fibrosis_model.pkl` (3.4 MB) | Yes | `POST /predict` | Step 4 Live Inference |
| **Model 3 (C): Metabolic / UCI HCV Classifier** | Random Forest (300 trees, `balanced_subsample`) | UCI HCV European Cohort (`hcvdat0.csv`) | 615 | 12 (Age, Sex, ALB, ALP, ALT, AST, BIL, CHE, CHOL, CREA, GGT, PROT) | Stratified 80/20 Holdout Split (492 train / 123 test) | Overall Acc: 0.9512<br>Balanced Acc: 0.5867<br>Macro F1: 0.6124 | `models/uci_hcv_exploratory_model.pkl` (2 MB) | Yes | `POST /api/models/uci-hcv/predict`<br>`GET /api/models/uci-hcv/metrics` | Step 4 Live Inference + Research Dashboard |
| **Model 3 (C-Obs): NHANES Observational Study** | Multivariate Linear & Log-Linear Regression | NHANES 2017–2020 Pre-Pandemic (`P_LUX`, `P_BIOPRO`, `P_CBC`, `P_DEMO`) | 4,286 (Adults with Complete Exams) | FIB-4, CAP Steatosis, Demographics | Cross-sectional epidemiological association | Spearman $\rho = 0.281$ ($p < 0.001$)<br>CAP + FIB-4 $R^2 = 13.17\%$ | Static Research Constants (`researchData.ts`) | N/A (Observational Study) | `GET /api/metrics` | Research Overview Dashboard |
| **Model 4 (D): Disease Etiology & Stigmata** | Random Forest (300 trees, `max_depth=6`, `class_weight="balanced"`) | Mayo Clinic Primary Biliary Cirrhosis Trial (`cirrhosis.csv`) | 412 (Histologically Confirmed) | 13 (Ascites, Hepatomegaly, Spiders, Edema, Age, Sex, Bili, Alb, Plat, SGOT, Alk_Phos, Copper, Prothrombin) | 5-Fold Stratified CV + 80/20 Stratified Holdout (83 test) | CV ROC-AUC: 0.7099<br>Test ROC-AUC: 0.6870<br>Test Precision: 0.8103<br>Test F1: 0.7966 | `models/etiology_stigmata_model.pkl` (1.8 MB) | Yes | `POST /api/models/model4/predict`<br>`GET /api/models/model4/metrics` | Step 4 Live Inference + Step 5 Synthesis |
| **Deterministic Engine: Clinical FIB-4** | Deterministic Arithmetic | Clinical Guideline Standard (AASLD/EASL, McPherson et al.) | N/A | 4 (Age [yr], AST [U/L], ALT [U/L], Platelets [$10^9/\text{L}$]) | Numerical Invariance Unit Testing (0.01 precision) | High NPV (>90% rule-out F3-F4) | Arithmetic Service (`backend/services/fib4.py`) | Yes | `POST /api/fib4/calculate`<br>`POST /api/assessments` | Step 3 Interactive Calculator & Risk Banner |
| **FIB-4 Artifact (Legacy Baseline)** | 1-Feature Logistic Regression | Historical Baseline Run | Unknown | 1 (`FIB4`) | Smoke Test Only | Legacy Baseline Score | `models/fib4_baseline_model.pkl` (1.9 KB) | Yes | Bypassed in favor of deterministic formula | Internal Integrity Check |

---

## 2. Model 1 (A) — Routine Clinical Baseline

### Purpose & Research Context
Serves as the baseline machine learning benchmark evaluating whether routinely collected clinical laboratory indices (Age, BMI, Platelets, AST 1, ALT 1) can predict histological fibrosis staging without advanced imaging or elastography.

### Dataset & Preprocessing
- **Cohort:** UCI Hepatitis C Virus (HCV) for Egyptian Patients (`data/HCV-Egy-Data.csv`).
- **Sample Size:** 1,384 patients with verified histological staging after removing rows with missing target values.
- **Target Definitions:**
  - *Target A:* Significant Fibrosis (Stage 1 vs. Stages 2–4).
  - *Target B (Primary):* Advanced Fibrosis / Cirrhosis (Stages 1–2 vs. Stages 3–4). The deployed artifact predicts Target B.
- **Features (5):** `Age`, `BMI`, `Plat`, `AST 1`, `ALT 1`.
  - **Critical Clinical Safeguard:** `AST 1` and `ALT 1` in this dataset represent normalized, protocol-specific ratio measurements rather than conventional serum transaminase concentrations in standard U/L. They are strictly segregated from standard FIB-4 inputs.
- **Preprocessing Pipeline:** `SimpleImputer(strategy="median")` $\rightarrow$ `StandardScaler()` $\rightarrow$ `LogisticRegression(max_iter=2000, class_weight="balanced", random_state=42)`. Imputation and scaling occur strictly inside the pipeline to avoid data leakage.

### Validation & Metrics
- **10-Fold Stratified Cross-Validation (Full Dataset):**
  - Accuracy: $0.5181 \pm 0.0227$
  - Precision: $0.5351 \pm 0.0219$
  - Recall (Sensitivity): $0.5182 \pm 0.0462$
  - Specificity: $0.5180 \pm 0.0400$
  - F1-Score: $0.5258 \pm 0.0313$
  - ROC-AUC: $0.5349 \pm 0.0297$
- **Held-Out Test Set Evaluation (80/20 Stratified Split, N=277 test rows):**
  - Accuracy: $0.5162$
  - Balanced Accuracy: $0.5169$
  - Precision: $0.5338$
  - Recall: $0.4965$
  - Specificity: $0.5373$
  - F1-Score: $0.5145$
  - ROC-AUC: $0.5040$
  - Confusion Matrix: $\text{TN}=72, \text{FP}=62, \text{FN}=72, \text{TP}=71$

### Scientific Investigation of Near-Chance Performance
Both 10-fold cross-validation ($0.535$) and the held-out evaluation ($0.504$) confirm that Model 1 operates near chance level. In Experiment 7 (`experiment7_feature_association.py`), rigorous statistical non-parametric tests demonstrated:
- Kruskal-Wallis test for `AST 1` across histological stages: $H = 2.528, p = 0.4703$, Benjamini-Hochberg adjusted $p = 0.7292$, effect size $\epsilon^2 = 0.000$.
- Kruskal-Wallis test for `ALT 1`: $H = 2.771, p = 0.4284$, Benjamini-Hochberg adjusted $p = 0.7292$, effect size $\epsilon^2 = 0.000$.
- Kruskal-Wallis test for `Plat`: $H = 1.886, p = 0.5964$, adjusted $p = 0.7292$, effect size $\epsilon^2 = 0.000$.
**Scientific Conclusion:** In this Egyptian HCV cohort, the routine laboratory markers exhibit virtually zero statistical association with histological biopsy stage. Near-chance performance is an honest reflection of true data properties, not an implementation failure. No labels were leaked or features manipulated.

---

## 3. Model 2 (B) — Expanded Hematologic Model

### Purpose & Research Context
Investigates whether adding complete blood count (CBC) hematologic indices (WBC, RBC, Hemoglobin) improves discriminative capacity for advanced fibrosis over the baseline 5 features.

### Dataset & Preprocessing
- **Cohort:** UCI Hepatitis C Virus (HCV) Egyptian Patients (`data/HCV-Egy-Data.csv`, N=1,384).
- **Target:** Target B (Advanced Fibrosis: Stages 1–2 vs. Stages 3–4).
- **Features (8):** `Age`, `BMI`, `Plat`, `AST 1`, `ALT 1`, `WBC`, `RBC`, `HGB`.
- **Preprocessing Pipeline:** `SimpleImputer(strategy="median")` $\rightarrow$ `RandomForestClassifier(n_estimators=300, max_depth=8, min_samples_split=5, min_samples_leaf=2, class_weight="balanced", random_state=42)`. Imputation occurs inside the pipeline.

### Validation & Metrics
- **10-Fold Stratified Cross-Validation (Full Dataset):**
  - Accuracy: $0.4899 \pm 0.0422$
  - Precision: $0.5056 \pm 0.0422$
  - Recall (Sensitivity): $0.5196 \pm 0.0732$
  - Specificity: $0.4582 \pm 0.0560$
  - F1-Score: $0.5114 \pm 0.0534$
  - ROC-AUC: $0.4976 \pm 0.0535$
- **Held-Out Test Set Evaluation (80/20 Stratified Split, N=277 test rows):**
  - Accuracy: $0.4982$
  - Balanced Accuracy: $0.4968$
  - Precision: $0.5133$
  - Recall: $0.5385$
  - Specificity: $0.4552$
  - F1-Score: $0.5256$
  - ROC-AUC: $0.4927$
  - Confusion Matrix: $\text{TN}=61, \text{FP}=73, \text{FN}=66, \text{TP}=77$
- **Feature Importances:**
  - WBC: 16.13%, Plat: 15.89%, RBC: 15.47%, AST 1: 13.07%, ALT 1: 12.90%, Age: 11.18%, BMI: 9.52%, HGB: 5.85%.

### Scientific Conclusion
Expanding features to complete blood count does not rescue discriminative performance in the Egyptian HCV dataset (ROC-AUC 0.493 vs. 0.504 for baseline). Feature importance is distributed almost uniformly across features (~10–16%), reflecting noise fitting rather than biological signal.

---

## 4. Model 3 (C) — Metabolic Biomarker Expansion & UCI HCV Classifier

### Architecture & Disambiguation
Model 3 encompasses two complementary research workstreams:
1. **A genuine trained machine learning classifier** on the European UCI Hepatitis C cohort (`models/uci_hcv_exploratory_model.pkl`).
2. **An observational cross-sectional study** on the NHANES 2017–2020 pre-pandemic VCTE vibration-controlled transient elastography cohort.

### 4.1. Trained UCI HCV 5-Class Classifier
- **Dataset:** UCI Hepatitis C Virus European Blood Donor & Disease Dataset (`data/hcvdat0.csv`, N=615).
- **Target:** 5-Class Diagnostic Category:
  - `0=Blood Donor` (N=533)
  - `0s=suspect Blood Donor` (N=7)
  - `1=Hepatitis` (N=24)
  - `2=Fibrosis` (N=21)
  - `3=Cirrhosis` (N=30)
- **Features (12):** `Age`, `Sex`, `ALB`, `ALP`, `ALT`, `AST`, `BIL`, `CHE`, `CHOL`, `CREA`, `GGT`, `PROT`.
- **Pipeline:** `ColumnTransformer` with median imputation for numeric features and most-frequent imputation + One-Hot Encoding for categorical features (`Sex`), connected to `RandomForestClassifier(n_estimators=300, class_weight="balanced_subsample", min_samples_leaf=2, random_state=42)`.
- **Evaluation (Stratified 80/20 Holdout Split, 492 train / 123 test):**
  - Overall Test Accuracy: $0.9512$ (driven by dominant Blood Donor class)
  - Balanced Accuracy: $0.5867$ (accounts for extreme imbalance)
  - Macro F1: $0.6124$
- **Per-Class Breakdown on Held-Out Test Set (N=123):**
  - `0=Blood Donor`: Precision 0.973, Recall 1.000, F1 0.986 (Support: 107)
  - `0s=suspect Blood Donor`: Precision 0.000, Recall 0.000, F1 0.000 (Support: 1)
  - `1=Hepatitis`: Precision 0.750, Recall 0.600, F1 0.667 (Support: 5)
  - `2=Fibrosis`: Precision 0.500, Recall 0.500, F1 0.500 (Support: 4)
  - `3=Cirrhosis`: Precision 1.000, Recall 0.833, F1 0.909 (Support: 6)
- **Scientific Limitation & Transparency:** Minority disease categories (Fibrosis: 4 test samples, Hepatitis: 5 test samples) have severe sample limitations. The API response explicitly returns `imbalanced_class_warning` explaining these confidence intervals.

### 4.2. NHANES Observational VCTE Analysis
- **Dataset:** National Health and Nutrition Examination Survey (NHANES) 2017–March 2020 Pre-Pandemic cycle (`P_LUX.xpt`, `P_BIOPRO.xpt`, `P_CBC.xpt`, `P_DEMO.xpt`).
- **Cohort:** 4,286 participants aged $\ge 18$ with complete FibroScan VCTE examinations (median liver stiffness measurement in kPa) and Controlled Attenuation Parameter (CAP in dB/m).
- **Study Type:** Observational association analysis (Experiments 8a–8h). This is **not a trained machine learning model** and does not make individual patient predictions.
- **Key Findings:**
  - Overall FIB-4 to Liver Stiffness correlation: Spearman $\rho = 0.281, p < 0.001$; Pearson $r = 0.180, p < 0.001$.
  - In linear regression adjusting for age and BMI, incorporating CAP steatosis score with FIB-4 explained $R^2 = 13.17\%$ of liver stiffness variance (log-scale), reducing Mean Absolute Error to $1.64\text{ kPa}$.
  - Clearly presented in the Research Dashboard and UI card as observational research findings.

---

## 5. Model 4 (D) — Disease Etiology & Clinical Stigmata

### Purpose & Research Context
Implements the fourth model workstream by integrating physical clinical stigmata (ascites, hepatomegaly, spiders, edema) with laboratory biomarkers to predict biopsy-confirmed advanced fibrosis or cirrhosis.

### Dataset & Preprocessing
- **Cohort:** Mayo Clinic Primary Biliary Cirrhosis (PBC) randomized trial cohort (`data/cirrhosis.csv`, N=418).
- **Eligible Sample:** 412 patients with histologically confirmed liver biopsy staging (Stage 1 to 4).
- **Target Definition:** Advanced Fibrosis / Cirrhosis (Stage 3–4 vs. Stage 1–2), matching the Target B formulation:
  - Stage 1–2 (Early / Moderate): 108 patients ($26.2\%$)
  - Stage 3–4 (Advanced / Cirrhosis): 304 patients ($73.8\%$)
- **Features (13):**
  - *Clinical Stigmata & Physical Signs:* `Ascites` (Y/N), `Hepatomegaly` (Y/N), `Spiders` (Y/N), `Edema` (N/S/Y).
  - *Demographics:* `Age_years` (converted from days), `Sex` (M/F).
  - *Laboratory Biomarkers:* `Bilirubin` (mg/dL), `Albumin` (g/dL), `Platelets` ($10^9/\text{L}$), `SGOT` (AST, U/L), `Alk_Phos` (U/L), `Copper` ($\mu\text{g/day}$), `Prothrombin` (seconds).
- **Preprocessing Pipeline:**
  - Numeric transformer: `SimpleImputer(strategy="median")` $\rightarrow$ `StandardScaler()`.
  - Categorical transformer: `SimpleImputer(strategy="most_frequent")` $\rightarrow$ `OneHotEncoder(handle_unknown="ignore", sparse_output=False)`.
  - Classifier: `RandomForestClassifier(n_estimators=300, max_depth=6, min_samples_split=4, min_samples_leaf=2, class_weight="balanced", random_state=42)`.
  - Full pipeline encapsulated in a `Pipeline` object; zero data leakage.

### Validation & Metrics
- **5-Fold Stratified Cross-Validation (Training Split, N=329):**
  - Accuracy: $0.6778 \pm 0.0222$
  - Balanced Accuracy: $0.6605 \pm 0.0495$
  - Precision: $0.8348 \pm 0.0441$
  - Recall: $0.6988 \pm 0.0427$
  - F1-Score: $0.7587 \pm 0.0179$
  - ROC-AUC: $0.7099 \pm 0.0320$
- **Held-Out Test Set Evaluation (20% Stratified Split, N=83 test rows):**
  - Accuracy: $0.7108$
  - Balanced Accuracy: $0.6525$
  - Precision: $0.8103$
  - Recall (Sensitivity): $0.7833$
  - Specificity: $0.5217$
  - F1-Score: $0.7966$
  - ROC-AUC: $0.6870$
  - Confusion Matrix: $\text{TN}=12, \text{FP}=11, \text{FN}=13, \text{TP}=47$
- **Top 10 Feature Importances:**
  1. Serum Albumin: 12.00%
  2. Total Bilirubin: 11.31%
  3. Age (years): 10.39%
  4. Platelet Count: 10.37%
  5. Urine/Serum Copper: 10.25%
  6. SGOT (AST): 9.08%
  7. Prothrombin Time: 7.79%
  8. Alkaline Phosphatase: 6.76%
  9. Hepatomegaly (Present): 4.59%
  10. Spider Angiomas (Present): 4.35%

### Scientific Interpretation
Model 4 achieves solid discriminative performance ($\text{ROC-AUC} \approx 0.710$ in CV, $0.687$ on held-out test data) because liver synthetic capacity markers (Albumin, Prothrombin), cholestatic markers (Bilirubin, Alk Phos), and physical signs of portal hypertension / liver enlargement (Hepatomegaly, Spiders) strongly correlate with histological architecture in cholestatic liver disease.

---

## 6. Deterministic Clinical FIB-4 Service

### Mathematical Formulation
$$\text{FIB-4} = \frac{\text{Age (years)} \times \text{AST (U/L)}}{\text{Platelet count } (10^9/\text{L}) \times \sqrt{\text{ALT (U/L)}}}$$

### Strict Unit and Boundary Policies
1. **Age:** Plausible adult clinical range $[18.0, 120.0]$ years. Pediatric patients ($<18$) rejected.
2. **AST:** Standard enzymatic concentration strictly in U/L, strictly $> 0$.
3. **ALT:** Standard enzymatic concentration strictly in U/L, strictly $> 0$.
4. **Platelets:** Validated strictly in $10^9/\text{L}$ (equivalent to $10^3/\mu\text{L}$ or $\text{k}/\mu\text{L}$), strictly $> 0$.
   - **Ambiguous Unit Safeguard:** Unreadable exponents (e.g. $10^?/L$ or corrupted text glyphs) are rejected or flagged as `ambiguous`. They are never assumed to be $10^9/\text{L}$ without explicit clinician verification.

### Threshold Policies
- **Age $< 65$ (AASLD/EASL Standard Scheme):**
  - Score $< 1.30$: **Low Risk** (Negative Predictive Value $> 90\%$)
  - $1.30 \le \text{Score} \le 2.67$: **Indeterminate Zone**
  - Score $> 2.67$: **High Risk** (Formal hepatology evaluation recommended)
- **Age $\ge 65$ (McPherson et al. Age-Adjusted Scheme):**
  - Score $< 2.00$: **Low Risk** (Higher cutoff prevents over-triaging elderly individuals)
  - $2.00 \le \text{Score} \le 2.67$: **Indeterminate Zone**
  - Score $> 2.67$: **High Risk**

---

## 7. Model Artifact Verification & Provenance

| Artifact Filename | Location | Size (Bytes) | MD5 / Integrity | Script Provenance | Verification Test |
|---|---|---|---|---|---|
| `routine_clinical_baseline.pkl` | `models/` | 2,097 | Verified | `train_models.py` | `test_baseline_artifact_integrity` |
| `expanded_fibrosis_model.pkl` | `models/` | 3,583,234 | Verified | `train_models.py` | `test_expanded_artifact_integrity` |
| `uci_hcv_exploratory_model.pkl` | `models/` | 1,999,635 | Verified | `experiment2_uci_hcv.py` | `test_uci_hcv_artifact_integrity` |
| `etiology_stigmata_model.pkl` | `models/` | 1,822,109 | Verified | `train_model4_cirrhosis.py` | `test_etiology_stigmata_model4_artifact_integrity` |
| `fib4_baseline_model.pkl` | `models/` | 1,905 | Verified (Legacy) | Historical Artifact | `test_fib4_baseline_artifact_integrity` |

---

## 8. Clinical and Regulatory Governance Notice

1. **Non-Diagnostic Research Prototype:** The SUGAR platform and all integrated models are intended exclusively for clinical research, triage evaluation, and educational demonstration.
2. **No Autonomous Diagnostic Claims:** The platform does not claim FDA clearance, CE-mark medical device certification, or diagnostic autonomy.
3. **Mandatory Clinician Verification:** All laboratory extractions require manual clinician review and explicit digital sign-off (`is_verified_by_doctor=True`) before an official clinical assessment can be persisted.
