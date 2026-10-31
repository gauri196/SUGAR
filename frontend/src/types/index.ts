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

// ---------------------------------------------------------------------------
// Backend Extraction Schemas
// ---------------------------------------------------------------------------

export type FieldStatus = 'valid' | 'invalid' | 'ambiguous' | 'absent';
export type ExtractionStatus = 'parsed' | 'partial' | 'no_text_found' | 'unsupported_format' | 'failed';

export interface ExtractedField {
  field_name: string;
  source_field?: string;
  raw_value?: string;
  interpreted_value?: number;
  unit?: string;
  status: FieldStatus;
  source_snippet?: string;
  error_message?: string;
}

export interface ExtractionResponse {
  success: boolean;
  extraction_status: ExtractionStatus;
  filename: string;
  media_type: string;
  file_size_bytes: number;
  extracted_fields: Record<string, ExtractedField>;
  clinical_values: Record<string, number | null>;
  missing_fields: string[];
  unresolved_fields: string[];
  warnings: string[];
  errors: string[];
  is_verified: boolean;
  requires_clinician_verification: boolean;
  verification_disclaimer: string;
}

// ---------------------------------------------------------------------------
// Backend Clinical Observation & Orchestration Schemas
// ---------------------------------------------------------------------------

export interface ClinicalObservationPayload {
  age_years?: number | null;
  bmi?: number | null;
  platelets_10e9_l?: number | null;
  ast_u_l?: number | null;
  alt_u_l?: number | null;
  wbc_10e9_l?: number | null;
  rbc_10e12_l?: number | null;
  hgb_g_dl?: number | null;
  glucose_mg_dl?: number | null;
  cholesterol_mg_dl?: number | null;
  cap_steatosis_dbm?: number | null;
  etiology?: string | null;
  ascites?: boolean | null;
  jaundice?: boolean | null;
  hepatomegaly?: boolean | null;
}

export interface ReportRegistrationRequest {
  external_subject_id?: string;
  patient_id?: string;
  original_filename: string;
  media_type?: string;
  file_size_bytes?: number;
  file_sha256?: string;
  extraction_status?: string;
  clinical_values?: ClinicalObservationPayload;
  field_provenance_json?: string;
  uploaded_by?: string;
  idempotency_key?: string;
}

export interface ReportRegistrationResponse {
  success: boolean;
  report_id: string;
  patient_id: string;
  observation_id: string;
  extraction_status: string;
  is_verified: boolean;
  message: string;
}

export interface ReportDetailResponse {
  id: string;
  patient_id: string;
  original_filename: string;
  media_type: string;
  file_size_bytes: number;
  extraction_status: string;
  uploaded_by?: string;
  created_at: string;
  observation?: Record<string, any>;
}

export interface ObservationVerificationRequest {
  verified_by: string;
  verified_values?: ClinicalObservationPayload;
  clinician_notes?: string;
}

export interface ObservationVerificationResponse {
  success: boolean;
  observation_id: string;
  patient_id: string;
  is_verified_by_doctor: boolean;
  verified_by: string;
  verified_at: string;
  clinical_values: Record<string, number | null>;
  message: string;
}

export interface AssessmentCreateRequest {
  patient_id: string;
  observation_id: string;
  clinician_notes?: string;
}

export interface AssessmentDetailResponse {
  id: string;
  patient_id: string;
  observation_id: string;
  fib4_score: number;
  fib4_risk_category: 'Low Risk' | 'Indeterminate' | 'High Risk';
  fib4_cutoff_applied: string;
  concordance_summary?: string;
  clinician_notes?: string;
  status: string;
  created_at: string;
  observation_values?: Record<string, number | null>;
  disclaimer: string;
}

export interface AssessmentListResponse {
  patient_id: string;
  total: number;
  items: AssessmentDetailResponse[];
}

export interface Fib4CalculationResponse {
  score: number;
  score_display: number;
  risk_category: 'Low Risk' | 'Indeterminate' | 'High Risk';
  threshold_set: {
    scheme_name: string;
    age_group: string;
    low_cutoff: number;
    high_cutoff: number;
    boundary_rules: string;
    citation: string;
  };
  interpretation: string;
  explanation: string;
  disclaimer: string;
}

export interface ClinicalInputs extends PatientData {
  // Metabolic variables (Model C research context)
  glucose?: number;
  cholesterol?: number;
  capSteatosis?: number;
  // Disease etiology & clinical context (Model D planned context)
  etiology?: 'hcv' | 'hbv' | 'mash' | 'alcohol' | 'cryptogenic' | 'other';
  ascites?: boolean;
  jaundice?: boolean;
  hepatomegaly?: boolean;
  // Metadata & Backend Persistence Links
  reportSource?: 'manual' | 'csv' | 'json' | 'pdf' | 'sample';
  reportFilename?: string;
  verifiedByDoctor: boolean;
  reportId?: string;
  patientId?: string;
  observationId?: string;
  assessmentId?: string;
  verifiedBy?: string;
  verifiedAt?: string;
  clinicianNotes?: string;
  extractedFields?: Record<string, ExtractedField>;
}

export type AssessmentStep = 1 | 2 | 3 | 4 | 5;

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

export interface UciHcvPredictionResponse {
  model_name: string;
  predicted_category: string;
  class_probabilities: Record<string, number>;
  top_probability: number;
  is_fibrosis_or_cirrhosis: boolean;
  scientific_disclaimer: string;
  imbalanced_class_warning: string;
}

export interface Model4PredictionResponse {
  model_name: string;
  prediction: number;
  risk_label: string;
  probability: number;
  stigmata_evaluated: Record<string, string>;
  dataset_provenance: string;
  scientific_disclaimer: string;
}

