// SUGAR — Verified Research Data Extracted from outputs/ and models/metrics.json
import {
  NhanesOverallAssociation,
  NhanesAgeGroupSummary,
  NhanesAdjustedModel,
  NhanesFairModelComparison,
  ExperimentSummaryRow,
  FeatureImportanceItem,
  OrganInfo,
} from '../types';

// ============================================================
// 1. NHANES 2017–2020 Real Results (7,211 Adult Participants)
// ============================================================

export const NHANES_OVERALL_ASSOCIATION: NhanesOverallAssociation = {
  participants: 7211,
  spearman_rho: 0.12176,
  spearman_p_value: 3.171e-25,
  pearson_r: 0.16481,
  pearson_p_value: 4.414e-45,
};

export const NHANES_AGE_GROUP_SUMMARY: NhanesAgeGroupSummary[] = [
  {
    age_group: '18-29',
    participants: 1359,
    median_fib4: 0.42,
    median_stiffness_kpa: 4.7,
    mean_fib4: 0.46,
    mean_stiffness_kpa: 5.22,
  },
  {
    age_group: '30-39',
    participants: 1075,
    median_fib4: 0.60,
    median_stiffness_kpa: 4.9,
    mean_fib4: 0.65,
    mean_stiffness_kpa: 5.42,
  },
  {
    age_group: '40-49',
    participants: 1120,
    median_fib4: 0.78,
    median_stiffness_kpa: 4.9,
    mean_fib4: 0.85,
    mean_stiffness_kpa: 5.41,
  },
  {
    age_group: '50-59',
    participants: 1215,
    median_fib4: 1.04,
    median_stiffness_kpa: 5.1,
    mean_fib4: 1.20,
    mean_stiffness_kpa: 6.10,
  },
  {
    age_group: '60-69',
    participants: 1344,
    median_fib4: 1.26,
    median_stiffness_kpa: 5.2,
    mean_fib4: 1.42,
    mean_stiffness_kpa: 6.45,
  },
  {
    age_group: '70-80',
    participants: 1098,
    median_fib4: 1.73,
    median_stiffness_kpa: 5.2,
    mean_fib4: 1.91,
    mean_stiffness_kpa: 6.16,
  },
];

export const NHANES_ADJUSTED_MODELS: NhanesAdjustedModel[] = [
  {
    model: 'Model 1: FIB-4 only',
    participants: 7211,
    log_fib4_coefficient: 0.1042,
    robust_ci_lower: 0.0867,
    robust_ci_upper: 0.1217,
    p_value: 1.688e-31,
    r_squared: 0.0266,
  },
  {
    model: 'Model 2: Adjusted for Age and Sex',
    participants: 7211,
    log_fib4_coefficient: 0.0824,
    robust_ci_lower: 0.0490,
    robust_ci_upper: 0.1158,
    p_value: 1.365e-6,
    r_squared: 0.0425,
  },
  {
    model: 'Model 3: Adjusted for Age, Sex, and CAP (Steatosis)',
    participants: 7210,
    log_fib4_coefficient: 0.1387,
    robust_ci_lower: 0.1061,
    robust_ci_upper: 0.1713,
    p_value: 7.864e-17,
    r_squared: 0.1300,
  },
];

export const NHANES_FAIR_MODEL_COMPARISON: NhanesFairModelComparison[] = [
  {
    model: 'Model 1: Age + Sex',
    training_participants: 5768,
    test_participants: 1442,
    test_mae_kpa: 1.7231,
    test_rmse_kpa: 4.4070,
    test_r2_log_scale: 0.0280,
    mae_improvement_pct: 0.0,
    rmse_improvement_pct: 0.0,
  },
  {
    model: 'Model 2: Age + Sex + FIB-4',
    training_participants: 5768,
    test_participants: 1442,
    test_mae_kpa: 1.7226,
    test_rmse_kpa: 4.3632,
    test_r2_log_scale: 0.0423,
    mae_improvement_pct: 0.03,
    rmse_improvement_pct: 0.99,
  },
  {
    model: 'Model 3: Age + Sex + FIB-4 + CAP',
    training_participants: 5768,
    test_participants: 1442,
    test_mae_kpa: 1.6432,
    test_rmse_kpa: 4.2800,
    test_r2_log_scale: 0.1317,
    mae_improvement_pct: 4.64,
    rmse_improvement_pct: 2.88,
  },
];

// ============================================================
// 2. Egyptian HCV Cohort Benchmarks (HCV-Egy-Data.csv, 1,385 Patients)
// ============================================================

export const EXPERIMENT3_FOUR_MODEL_SUMMARY: ExperimentSummaryRow[] = [
  {
    target: 'Target A (Stage 1 vs 2-4)',
    model: 'Baseline',
    features: 'Age, BMI, Plat, AST 1, ALT 1',
    algorithm: 'Logistic Regression',
    accuracy: 0.5058,
    accuracy_std: 0.0339,
    precision: 0.7614,
    precision_std: 0.0335,
    sensitivity: 0.5067,
    sensitivity_std: 0.0394,
    specificity: 0.5029,
    specificity_std: 0.0861,
    f1: 0.6077,
    f1_std: 0.0324,
    roc_auc: 0.4900,
    roc_auc_std: 0.0526,
  },
  {
    target: 'Target A (Stage 1 vs 2-4)',
    model: 'Expanded',
    features: 'Baseline + WBC, RBC, HGB',
    algorithm: 'Logistic Regression',
    accuracy: 0.4776,
    accuracy_std: 0.0311,
    precision: 0.7331,
    precision_std: 0.0217,
    sensitivity: 0.4876,
    sensitivity_std: 0.0520,
    specificity: 0.4463,
    specificity_std: 0.0692,
    f1: 0.5843,
    f1_std: 0.0405,
    roc_auc: 0.4510,
    roc_auc_std: 0.0363,
  },
  {
    target: 'Target A (Stage 1 vs 2-4)',
    model: 'Baseline',
    features: 'Age, BMI, Plat, AST 1, ALT 1',
    algorithm: 'Random Forest',
    accuracy: 0.6294,
    accuracy_std: 0.0364,
    precision: 0.7670,
    precision_std: 0.0314,
    sensitivity: 0.7347,
    sensitivity_std: 0.0302,
    specificity: 0.3010,
    specificity_std: 0.1194,
    f1: 0.7501,
    f1_std: 0.0243,
    roc_auc: 0.5237,
    roc_auc_std: 0.0522,
  },
  {
    target: 'Target A (Stage 1 vs 2-4)',
    model: 'Expanded',
    features: 'Baseline + WBC, RBC, HGB',
    algorithm: 'Random Forest',
    accuracy: 0.6445,
    accuracy_std: 0.0322,
    precision: 0.7550,
    precision_std: 0.0190,
    sensitivity: 0.7853,
    sensitivity_std: 0.0343,
    specificity: 0.2058,
    specificity_std: 0.0572,
    f1: 0.7696,
    f1_std: 0.0235,
    roc_auc: 0.4748,
    roc_auc_std: 0.0536,
  },
  {
    target: 'Target B (Stages 1-2 vs 3-4)',
    model: 'Baseline',
    features: 'Age, BMI, Plat, AST 1, ALT 1',
    algorithm: 'Logistic Regression',
    accuracy: 0.5181,
    accuracy_std: 0.0239,
    precision: 0.5351,
    precision_std: 0.0231,
    sensitivity: 0.5182,
    sensitivity_std: 0.0487,
    specificity: 0.5180,
    specificity_std: 0.0422,
    f1: 0.5258,
    f1_std: 0.0330,
    roc_auc: 0.5349,
    roc_auc_std: 0.0314,
  },
  {
    target: 'Target B (Stages 1-2 vs 3-4)',
    model: 'Expanded',
    features: 'Baseline + WBC, RBC, HGB',
    algorithm: 'Logistic Regression',
    accuracy: 0.5203,
    accuracy_std: 0.0228,
    precision: 0.5377,
    precision_std: 0.0229,
    sensitivity: 0.5280,
    sensitivity_std: 0.0269,
    specificity: 0.5120,
    specificity_std: 0.0485,
    f1: 0.5324,
    f1_std: 0.0191,
    roc_auc: 0.5195,
    roc_auc_std: 0.0310,
  },
  {
    target: 'Target B (Stages 1-2 vs 3-4)',
    model: 'Baseline',
    features: 'Age, BMI, Plat, AST 1, ALT 1',
    algorithm: 'Random Forest',
    accuracy: 0.5203,
    accuracy_std: 0.0442,
    precision: 0.5353,
    precision_std: 0.0420,
    sensitivity: 0.5518,
    sensitivity_std: 0.0601,
    specificity: 0.4866,
    specificity_std: 0.0599,
    f1: 0.5427,
    f1_std: 0.0466,
    roc_auc: 0.5088,
    roc_auc_std: 0.0521,
  },
  {
    target: 'Target B (Stages 1-2 vs 3-4)',
    model: 'Expanded',
    features: 'Baseline + WBC, RBC, HGB',
    algorithm: 'Random Forest',
    accuracy: 0.4899,
    accuracy_std: 0.0445,
    precision: 0.5056,
    precision_std: 0.0445,
    sensitivity: 0.5196,
    sensitivity_std: 0.0772,
    specificity: 0.4582,
    specificity_std: 0.0591,
    f1: 0.5114,
    f1_std: 0.0563,
    roc_auc: 0.4976,
    roc_auc_std: 0.0564,
  },
];

export const FEATURE_IMPORTANCES: FeatureImportanceItem[] = [
  {
    feature: 'WBC',
    importance: 0.1613,
    description: 'White Blood Cell count (10^3/uL) - systemic inflammatory state.',
  },
  {
    feature: 'Plat',
    importance: 0.1589,
    description: 'Platelet count (10^3/uL) - sensitive marker of portal hypertension and splenic sequestration.',
  },
  {
    feature: 'RBC',
    importance: 0.1547,
    description: 'Red Blood Cell count (10^6/uL) - hematological marrow response.',
  },
  {
    feature: 'AST 1',
    importance: 0.1307,
    description: 'Dataset-specific ratio variable reflecting aspartate aminotransferase activity.',
  },
  {
    feature: 'ALT 1',
    importance: 0.1290,
    description: 'Dataset-specific ratio variable reflecting alanine aminotransferase activity.',
  },
  {
    feature: 'Age',
    importance: 0.1118,
    description: 'Patient age in years - cumulative hepatic injury duration.',
  },
  {
    feature: 'BMI',
    importance: 0.0952,
    description: 'Body Mass Index (kg/m^2) - co-occurring metabolic steatosis risk.',
  },
  {
    feature: 'HGB',
    importance: 0.0585,
    description: 'Hemoglobin concentration (g/dL) - oxygenation and chronic disease marker.',
  },
];

// ============================================================
// 3. Anatomical Organs Directory with Natural Biological Colors
// ============================================================

export const ANATOMICAL_ORGANS: OrganInfo[] = [
  {
    id: 'liver',
    name: 'Liver (Hepar)',
    system: 'Hepatobiliary / Digestive',
    naturalColor: '#78261F', // Deep rich reddish-brown hepatic hue
    colorName: 'Hepatic Reddish-Brown',
    position: [0.38, 0.18, 0.22],
    scale: [0.68, 0.54, 0.48],
    cameraTarget: [0.35, 0.15, 0.2],
    cameraDistance: 1.8,
    function:
      'Central metabolic processing hub: protein synthesis (albumin, clotting factors), xenobiotic detoxification, bile production, glycogen storage, and immune surveillance.',
    biomarkers: [
      {
        name: 'ALT (Alanine Aminotransferase)',
        normalRange: '7–55 U/L',
        fibrosisSignificance:
          'Hepatocellular membrane permeability; leaks into circulation during active injury.',
      },
      {
        name: 'AST (Aspartate Aminotransferase)',
        normalRange: '8–48 U/L',
        fibrosisSignificance:
          'Mitochondrial and cytosolic enzyme; AST/ALT ratio > 1 frequently heralds advanced architectural distortion.',
      },
      {
        name: 'VCTE Liver Stiffness (E)',
        normalRange: '2.0–6.0 kPa',
        fibrosisSignificance:
          'Transient elastography shear wave velocity measurement in kilopascals (kPa). Reflects physical extracellular matrix stiffness.',
      },
      {
        name: 'Controlled Attenuation Parameter (CAP)',
        normalRange: '100–238 dB/m',
        fibrosisSignificance:
          'Ultrasound attenuation reflecting hepatic steatosis (fat fraction), which significantly modulates stiffness readings.',
      },
    ],
    fibrosisNotes:
      'Progression entails activation of hepatic stellate cells into myofibroblasts, depositing cross-linked Type I/III collagen in the space of Disse. Early stages (F1–F2) feature portal and periportal expansion, advancing to bridging fibrosis (F3) and cirrhotic regenerative nodules with vascular distortion (F4).',
    disclaimer:
      'Scientific Note: In SUGAR, transient elastography stiffness (kPa) is treated as a continuous physical biomarker and NOT conflated with histological Metavir staging.',
  },
  {
    id: 'gallbladder',
    name: 'Gallbladder',
    system: 'Biliary',
    naturalColor: '#4E6830', // Olive-gold green
    colorName: 'Biliary Olive-Green',
    position: [0.24, -0.05, 0.35],
    scale: [0.18, 0.26, 0.18],
    cameraTarget: [0.24, -0.05, 0.35],
    cameraDistance: 1.2,
    function:
      'Concentrates and stores hepatic bile (~30–50 mL), rhythmically expelling it into the duodenum upon cholecystokinin release for lipid emulsification.',
    biomarkers: [
      {
        name: 'Total Bilirubin',
        normalRange: '0.2–1.2 mg/dL',
        fibrosisSignificance:
          'Elevation signals impaired hepatobiliary transport or extrahepatic cholestasis.',
      },
      {
        name: 'Alkaline Phosphatase (ALP)',
        normalRange: '44–147 U/L',
        fibrosisSignificance:
          'Canalicular membrane enzyme elevated during biliary stasis.',
      },
    ],
    fibrosisNotes:
      'Cirrhotic portal hypertension often causes gallbladder wall thickening, edema, and secondary biliary stasis without primary cholecystitis.',
    disclaimer:
      'Biliary dimensions visualized represent schematic anatomical orientations.',
  },
  {
    id: 'spleen',
    name: 'Spleen (Lien)',
    system: 'Lymphatic / Reticuloendothelial',
    naturalColor: '#5C2234', // Deep plum-maroon
    colorName: 'Plum Deep Red',
    position: [-0.62, 0.22, 0.05],
    scale: [0.35, 0.45, 0.32],
    cameraTarget: [-0.58, 0.2, 0.05],
    cameraDistance: 1.5,
    function:
      'Erythrocyte quality control (culling senescent RBCs), blood reservoir, and active lymphoid immune response against encapsulated bacteria.',
    biomarkers: [
      {
        name: 'Platelet Count (Plat)',
        normalRange: '150–450 x 10^3/uL',
        fibrosisSignificance:
          'Splenomegaly secondary to portal hypertension leads to progressive platelet sequestration, driving thrombocytopenia—the principal foundation of FIB-4.',
      },
      {
        name: 'Spleen Diameter',
        normalRange: '< 12 cm',
        fibrosisSignificance:
          'Ultrasonographic splenomegaly serves as a clinical surrogate for elevated hepatic venous pressure gradient (HVPG).',
      },
    ],
    fibrosisNotes:
      'As hepatic vascular resistance rises, back-pressure through the splenic vein induces congestive splenomegaly, hypersplenism, and marked platelet drops.',
    disclaimer:
      'Splenic biomarkers illustrate the pathophysiological rationale for platelet weighting in fibrosis scores.',
  },
  {
    id: 'stomach',
    name: 'Stomach (Gaster)',
    system: 'Digestive',
    naturalColor: '#B87262', // Warm visceral peach-tan
    colorName: 'Visceral Peach-Tan',
    position: [-0.15, 0.15, 0.26],
    scale: [0.48, 0.52, 0.42],
    cameraTarget: [-0.15, 0.15, 0.26],
    cameraDistance: 1.6,
    function:
      'Mechanical churn, gastric acid (HCl) secretion, pepsinogen activation, and intrinsic factor production for cobalamin absorption.',
    biomarkers: [
      {
        name: 'Gastric Mucosal Integrity',
        normalRange: 'Pink rugae, intact',
        fibrosisSignificance:
          'Portal hypertensive gastropathy (mosaic pattern) occurs when portal pressures exceed 10–12 mmHg.',
      },
    ],
    fibrosisNotes:
      'Collateral venous flow during advanced cirrhosis diverts portal blood through coronary and gastric veins, creating perilous gastroesophageal varices.',
    disclaimer: 'Gastric anatomical positioning is represented for structural contextualization.',
  },
  {
    id: 'kidney_right',
    name: 'Right Kidney (Ren Dexter)',
    system: 'Urinary / Endocrine',
    naturalColor: '#7A2C2C', // Renal dark crimson-brown
    colorName: 'Renal Crimson-Brown',
    position: [0.45, -0.28, -0.15],
    scale: [0.26, 0.42, 0.28],
    cameraTarget: [0.45, -0.28, -0.15],
    cameraDistance: 1.4,
    function:
      'Glomerular filtration, electrolyte balance, blood pressure regulation via renin-angiotensin-aldosterone axis, and erythropoietin secretion.',
    biomarkers: [
      {
        name: 'Serum Creatinine',
        normalRange: '0.6–1.2 mg/dL',
        fibrosisSignificance:
          'Core metric in MELD score; hepatorenal syndrome (HRS) reflects extreme splanchnic vasodilation causing severe renal vasoconstriction.',
      },
      {
        name: 'eGFR',
        normalRange: '> 90 mL/min/1.73m^2',
        fibrosisSignificance:
          'Renal perfusion diminishes precipitously in decompensated cirrhosis.',
      },
    ],
    fibrosisNotes:
      'Located inferior to the right hepatic lobe. In advanced cirrhosis, systemic vasodilation triggers intense renal cortical hypoperfusion.',
    disclaimer: 'Renal parameters are monitored in liver failure due to hepatorenal cross-talk.',
  },
  {
    id: 'kidney_left',
    name: 'Left Kidney (Ren Sinister)',
    system: 'Urinary / Endocrine',
    naturalColor: '#7A2C2C', // Renal dark crimson-brown
    colorName: 'Renal Crimson-Brown',
    position: [-0.45, -0.24, -0.15],
    scale: [0.26, 0.42, 0.28],
    cameraTarget: [-0.45, -0.24, -0.15],
    cameraDistance: 1.4,
    function:
      'Filters systemic metabolic waste, regulates acid-base homeostasis, maintains fluid osmolarity, and activates vitamin D.',
    biomarkers: [
      {
        name: 'Blood Urea Nitrogen (BUN)',
        normalRange: '7–20 mg/dL',
        fibrosisSignificance:
          'Prerenal azotemia indicator in cirrhotic fluid dysregulation.',
      },
    ],
    fibrosisNotes:
      'Slightly higher than right kidney due to absence of massive liver overhead.',
    disclaimer: 'Renal models represent bilateral symmetrical organs.',
  },
  {
    id: 'heart',
    name: 'Heart (Cor)',
    system: 'Cardiovascular',
    naturalColor: '#8E2028', // Cardiac muscle crimson
    colorName: 'Myocardial Crimson',
    position: [-0.05, 0.95, 0.12],
    scale: [0.38, 0.44, 0.36],
    cameraTarget: [-0.05, 0.95, 0.12],
    cameraDistance: 1.5,
    function:
      'Powers systemic and pulmonary perfusion. Delivers ~25% of resting cardiac output to the liver via the hepatic artery and portal system.',
    biomarkers: [
      {
        name: 'Cardiac Output',
        normalRange: '4.0–8.0 L/min',
        fibrosisSignificance:
          'Cirrhotic cardiomyopathy presents as hyperdynamic circulation with high resting cardiac output but blunted ventricular stress response.',
      },
    ],
    fibrosisNotes:
      'Hepatic cirrhosis induces chronic hyperdynamic circulation: systemic vascular resistance collapses while cardiac output paradoxically climbs.',
    disclaimer: 'Thoracic anatomical reference.',
  },
  {
    id: 'lungs',
    name: 'Lungs (Pulmones)',
    system: 'Respiratory',
    naturalColor: '#9C6267', // Pulmonary slate-rose
    colorName: 'Pulmonary Slate-Rose',
    position: [0.0, 0.95, -0.05],
    scale: [0.95, 0.65, 0.55],
    cameraTarget: [0.0, 0.95, 0.0],
    cameraDistance: 2.0,
    function:
      'Gas exchange across alveolar-capillary membranes; oxygenates hepatic arterial inflow.',
    biomarkers: [
      {
        name: 'Oxygen Saturation (SpO2)',
        normalRange: '95–100%',
        fibrosisSignificance:
          'Hepatopulmonary syndrome (HPS) presents with platypnea-orthodeoxia due to intrapulmonary vascular dilatations.',
      },
    ],
    fibrosisNotes:
      'Intrapulmonary microvascular dilatations occur in up to 30% of cirrhotic patients, causing functional right-to-left shunting.',
    disclaimer: 'Bilateral lung volume envelope.',
  },
];
