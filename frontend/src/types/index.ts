// SUGAR — Type Definitions

export interface PatientData {
  age: number;
  bmi: number;
  platelets: number;
  ast: number;
  alt: number;
  wbc: number;
  rbc: number;
  hgb: number;
}

export interface ModelPrediction {
  prediction: number;
  probability: number;
}

export interface PredictionResponse {
  baseline_model: ModelPrediction;
  expanded_model: ModelPrediction;
  disclaimer: string;
}

export interface OrganInfo {
  id: string;
  name: string;
  system: string;
  naturalColor: string;
  colorName: string;
  position: [number, number, number];
  scale: [number, number, number];
  cameraTarget: [number, number, number];
  cameraDistance: number;
  function: string;
  biomarkers: {
    name: string;
    normalRange: string;
    fibrosisSignificance: string;
  }[];
  fibrosisNotes: string;
  disclaimer: string;
}

export interface NhanesOverallAssociation {
  participants: number;
  spearman_rho: number;
  spearman_p_value: number;
  pearson_r: number;
  pearson_p_value: number;
}

export interface NhanesAgeGroupSummary {
  age_group: string;
  participants: number;
  median_fib4: number;
  median_stiffness_kpa: number;
  mean_fib4: number;
  mean_stiffness_kpa: number;
}

export interface NhanesAdjustedModel {
  model: string;
  participants: number;
  log_fib4_coefficient: number;
  robust_ci_lower: number;
  robust_ci_upper: number;
  p_value: number;
  r_squared: number;
}

export interface NhanesFairModelComparison {
  model: string;
  training_participants: number;
  test_participants: number;
  test_mae_kpa: number;
  test_rmse_kpa: number;
  test_r2_log_scale: number;
  mae_improvement_pct: number;
  rmse_improvement_pct: number;
}

export interface ExperimentSummaryRow {
  target: string;
  model: string;
  features: string;
  algorithm: string;
  accuracy: number;
  accuracy_std: number;
  precision: number;
  precision_std: number;
  sensitivity: number;
  sensitivity_std: number;
  specificity: number;
  specificity_std: number;
  f1: number;
  f1_std: number;
  roc_auc: number;
  roc_auc_std: number;
}

export interface FeatureImportanceItem {
  feature: string;
  importance: number;
  description: string;
}
