// SUGAR — API Service Layer
import {
  PatientData,
  PredictionResponse,
  ClinicalInputs,
  ClinicalObservationPayload,
  ExtractionResponse,
  ReportRegistrationRequest,
  ReportRegistrationResponse,
  ReportDetailResponse,
  ObservationVerificationRequest,
  ObservationVerificationResponse,
  AssessmentCreateRequest,
  AssessmentDetailResponse,
  AssessmentListResponse,
  Fib4CalculationResponse,
  Model4PredictionResponse,
  UciHcvPredictionResponse,
} from '../types';

export const API_BASE_URL = (import.meta as any).env?.VITE_API_BASE_URL || 'http://localhost:8000';

export async function checkBackendHealth(): Promise<{ online: boolean; message: string }> {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 2000);
    const res = await fetch(`${API_BASE_URL}/health`, { signal: controller.signal });
    clearTimeout(timeoutId);
    if (res.ok) {
      const data = await res.json();
      return { online: true, message: data.message || 'Connected to FastAPI backend' };
    }
    return { online: false, message: `Backend responded with HTTP ${res.status}` };
  } catch (_err) {
    return { online: false, message: 'Backend offline (run `uvicorn backend.main:app --reload`)' };
  }
}

export async function submitPrediction(patient: PatientData): Promise<{
  success: boolean;
  data: PredictionResponse;
  source: 'live' | 'fallback';
  error?: string;
}> {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 3500);

    const res = await fetch(`${API_BASE_URL}/predict`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(patient),
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (res.ok) {
      const data: PredictionResponse = await res.json();
      return { success: true, data, source: 'live' };
    } else {
      throw new Error(`Server returned HTTP ${res.status}`);
    }
  } catch (err: any) {
    // Scientific integrity: Do NOT fabricate probabilities when backend is offline
    return {
      success: false,
      data: {
        baseline_model: { prediction: 0, probability: 0 },
        expanded_model: { prediction: 0, probability: 0 },
        disclaimer: 'FastAPI backend connection error. Live model inference unavailable.',
      },
      source: 'live',
      error: err?.message || 'Connection to FastAPI backend failed (http://localhost:8000/predict).',
    };
  }
}

/**
 * Convert frontend ClinicalInputs to backend ClinicalObservationPayload (preserving nulls).
 */
export function clinicalInputsToObservationPayload(
  inputs: Partial<ClinicalInputs>
): ClinicalObservationPayload {
  return {
    age_years: inputs.age !== undefined && inputs.age > 0 ? inputs.age : null,
    bmi: inputs.bmi !== undefined && inputs.bmi > 0 ? inputs.bmi : null,
    platelets_10e9_l: inputs.platelets !== undefined && inputs.platelets > 0 ? inputs.platelets : null,
    ast_u_l: inputs.ast !== undefined && inputs.ast > 0 ? inputs.ast : null,
    alt_u_l: inputs.alt !== undefined && inputs.alt > 0 ? inputs.alt : null,
    wbc_10e9_l: inputs.wbc !== undefined && inputs.wbc > 0 ? inputs.wbc : null,
    rbc_10e12_l: inputs.rbc !== undefined && inputs.rbc > 0 ? inputs.rbc : null,
    hgb_g_dl: inputs.hgb !== undefined && inputs.hgb > 0 ? inputs.hgb : null,
    glucose_mg_dl: inputs.glucose !== undefined && inputs.glucose > 0 ? inputs.glucose : null,
    cholesterol_mg_dl: inputs.cholesterol !== undefined && inputs.cholesterol > 0 ? inputs.cholesterol : null,
    cap_steatosis_dbm: inputs.capSteatosis !== undefined && inputs.capSteatosis > 0 ? inputs.capSteatosis : null,
    etiology: inputs.etiology || null,
    ascites: inputs.ascites ?? null,
    jaundice: inputs.jaundice ?? null,
    hepatomegaly: inputs.hepatomegaly ?? null,
  };
}

/**
 * Extract structured laboratory parameters from a file (JSON, CSV, or digital PDF)
 * using the verified backend Phase 4 extraction pipeline.
 */
export async function extractReport(file: File): Promise<ExtractionResponse> {
  const formData = new FormData();
  formData.append('file', file);

  const res = await fetch(`${API_BASE_URL}/api/reports/extract`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const errorBody = await res.json().catch(() => ({}));
    throw new Error(errorBody.detail || `Report extraction failed with HTTP ${res.status}`);
  }

  return res.json();
}

/**
 * Register an extracted report and its raw, unverified observation in the database.
 */
export async function registerReport(
  data: ReportRegistrationRequest
): Promise<ReportRegistrationResponse> {
  const res = await fetch(`${API_BASE_URL}/api/reports/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });

  if (!res.ok) {
    const errorBody = await res.json().catch(() => ({}));
    throw new Error(errorBody.detail || `Report registration failed with HTTP ${res.status}`);
  }

  return res.json();
}

/**
 * Retrieve report details and linked observation by report ID.
 */
export async function getReportDetail(reportId: string): Promise<ReportDetailResponse> {
  const res = await fetch(`${API_BASE_URL}/api/reports/${reportId}`);
  if (!res.ok) {
    const errorBody = await res.json().catch(() => ({}));
    throw new Error(errorBody.detail || `Failed to fetch report HTTP ${res.status}`);
  }
  return res.json();
}

/**
 * Submit clinician verification / manual corrections for a specific observation.
 */
export async function verifyObservation(
  observationId: string,
  data: ObservationVerificationRequest
): Promise<ObservationVerificationResponse> {
  const res = await fetch(`${API_BASE_URL}/api/observations/${observationId}/verify`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });

  if (!res.ok) {
    const errorBody = await res.json().catch(() => ({}));
    throw new Error(errorBody.detail || `Observation verification failed with HTTP ${res.status}`);
  }

  return res.json();
}

/**
 * Orchestrate clinical assessment calculation and persistence from a verified observation.
 */
export async function createAssessment(
  data: AssessmentCreateRequest
): Promise<AssessmentDetailResponse> {
  const res = await fetch(`${API_BASE_URL}/api/assessments`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });

  if (!res.ok) {
    const errorBody = await res.json().catch(() => ({}));
    throw new Error(errorBody.detail || `Assessment creation failed with HTTP ${res.status}`);
  }

  return res.json();
}

/**
 * Retrieve assessment record with linked observation values.
 */
export async function getAssessmentDetail(
  assessmentId: string
): Promise<AssessmentDetailResponse> {
  const res = await fetch(`${API_BASE_URL}/api/assessments/${assessmentId}`);
  if (!res.ok) {
    const errorBody = await res.json().catch(() => ({}));
    throw new Error(errorBody.detail || `Failed to fetch assessment HTTP ${res.status}`);
  }
  return res.json();
}

/**
 * Retrieve paginated historical assessments for a patient.
 */
export async function getPatientAssessments(
  patientId: string,
  skip = 0,
  limit = 20
): Promise<AssessmentListResponse> {
  const res = await fetch(
    `${API_BASE_URL}/api/patients/${patientId}/assessments?skip=${skip}&limit=${limit}`
  );
  if (!res.ok) {
    const errorBody = await res.json().catch(() => ({}));
    throw new Error(errorBody.detail || `Failed to fetch patient history HTTP ${res.status}`);
  }
  return res.json();
}

/**
 * Query backend FIB-4 calculation service directly.
 */
export async function calculateFib4Backend(
  age: number,
  ast: number,
  alt: number,
  platelets: number
): Promise<Fib4CalculationResponse> {
  const res = await fetch(`${API_BASE_URL}/api/fib4/calculate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ age, ast, alt, platelets }),
  });
  if (!res.ok) {
    const errorBody = await res.json().catch(() => ({}));
    throw new Error(errorBody.detail || `FIB-4 calculation failed with HTTP ${res.status}`);
  }
  return res.json();
}

/**
 * Standard Clinical FIB-4 Formula:
 * FIB-4 = (Age [years] * AST [U/L]) / (Platelet count [10^9/L] * sqrt(ALT [U/L]))
 */
export function calculateFib4(age: number, ast: number, alt: number, platelets: number): number {
  if (platelets <= 0 || alt <= 0 || age <= 0) return 0;
  const fib4 = (age * ast) / (platelets * Math.sqrt(alt));
  return Number(fib4.toFixed(2));
}

export function interpretFib4(fib4: number, age?: number): {
  category: 'Low Risk' | 'Indeterminate' | 'High Risk';
  description: string;
  recommendation: string;
  colorClass: string;
} {
  // Clinical guidelines: For individuals aged >= 65, the lower cutoff is adjusted to 2.0 to avoid false positives
  const lowCutoff = age && age >= 65 ? 2.0 : 1.3;

  if (fib4 < lowCutoff) {
    return {
      category: 'Low Risk',
      description: `FIB-4 < ${lowCutoff.toFixed(2)}: High negative predictive value (~90–95%) in primary care populations; NPV varies with disease prevalence and is not universally guaranteed.`,
      recommendation: 'Routine follow-up in primary care; secondary imaging or hepatology referral is typically not required unless red-flag signs develop.',
      colorClass: 'text-emerald-400 border-emerald-500/40 bg-emerald-950/20',
    };
  } else if (fib4 <= 2.67) {
    return {
      category: 'Indeterminate',
      description: `FIB-4 ${lowCutoff.toFixed(2)}–2.67: Indeterminate zone. Serum aminotransferases and platelet indices alone cannot reliably rule in or rule out advanced fibrosis.`,
      recommendation: 'Clinical guidelines (AASLD/EASL) recommend secondary non-invasive testing (such as VCTE FibroScan elastography, ELF score, or MRE) before liver biopsy.',
      colorClass: 'text-amber-300 border-amber-500/40 bg-amber-950/20',
    };
  } else {
    return {
      category: 'High Risk',
      description: 'FIB-4 > 2.67: High specificity (>80%) for advanced fibrosis / cirrhosis (Metavir F3–F4).',
      recommendation: 'Hepatology evaluation recommended for formal staging, screening for portal hypertension (varices), and hepatocellular carcinoma (HCC) ultrasound surveillance.',
      colorClass: 'text-rose-400 border-rose-500/40 bg-rose-950/20',
    };
  }
}

/**
 * Model 3: UCI HCV 5-Class Classifier API client.
 */
export async function predictUciHcv(payload: {
  age: number;
  sex?: string;
  alb?: number;
  alp?: number;
  alt?: number;
  ast?: number;
  bil?: number;
  che?: number;
  chol?: number;
  crea?: number;
  ggt?: number;
  prot?: number;
}): Promise<UciHcvPredictionResponse> {
  const res = await fetch(`${API_BASE_URL}/api/models/uci-hcv/predict`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `UCI HCV inference failed with HTTP ${res.status}`);
  }
  return res.json();
}

export async function fetchUciHcvMetrics(): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/api/models/uci-hcv/metrics`);
  if (!res.ok) throw new Error(`Failed to fetch UCI HCV metrics: HTTP ${res.status}`);
  return res.json();
}

/**
 * Model 4: Disease Etiology & Clinical Stigmata API client.
 */
export async function predictModel4(payload: {
  age_years: number;
  sex?: string;
  bilirubin?: number;
  albumin?: number;
  platelets?: number;
  sgot?: number;
  alk_phos?: number;
  copper?: number;
  prothrombin?: number;
  ascites?: string;
  hepatomegaly?: string;
  spiders?: string;
  edema?: string;
}): Promise<Model4PredictionResponse> {
  const res = await fetch(`${API_BASE_URL}/api/models/model4/predict`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Model 4 inference failed with HTTP ${res.status}`);
  }
  return res.json();
}

export async function fetchModel4Metrics(): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/api/models/model4/metrics`);
  if (!res.ok) throw new Error(`Failed to fetch Model 4 metrics: HTTP ${res.status}`);
  return res.json();
}

