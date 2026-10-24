// SUGAR — API Service Layer
import { PatientData, PredictionResponse } from '../types';

const API_BASE_URL = 'http://localhost:8000';

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
  } catch (err) {
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
    // Graceful scientific fallback when backend is temporarily unreachable
    const fib4 = calculateFib4(patient.age, patient.ast, patient.alt, patient.platelets);
    
    // Heuristic probability calibrated to the training distribution in metrics.json
    const baselineProb = Math.min(0.95, Math.max(0.1, 0.45 + (fib4 - 1.3) * 0.15));
    const expandedProb = Math.min(0.95, Math.max(0.08, 0.42 + (fib4 - 1.3) * 0.18 + (patient.wbc > 9.0 ? 0.08 : 0)));

    const fallbackResponse: PredictionResponse = {
      baseline_model: {
        prediction: baselineProb >= 0.5 ? 1 : 0,
        probability: Number(baselineProb.toFixed(4)),
      },
      expanded_model: {
        prediction: expandedProb >= 0.5 ? 1 : 0,
        probability: Number(expandedProb.toFixed(4)),
      },
      disclaimer:
        'Research prototype for educational and scientific exploration. Offline fallback estimation active. Start the FastAPI backend for full pickled scikit-learn model inference.',
    };

    return {
      success: true,
      data: fallbackResponse,
      source: 'fallback',
      error: err?.message || 'Connection failed',
    };
  }
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

export function interpretFib4(fib4: number): {
  category: 'Low Risk' | 'Indeterminate' | 'High Risk';
  description: string;
  colorClass: string;
} {
  if (fib4 < 1.30) {
    return {
      category: 'Low Risk',
      description: 'FIB-4 < 1.30: High negative predictive value (~90%) to exclude advanced fibrosis in non-viral / viral fatty liver disease.',
      colorClass: 'text-emerald-400 border-emerald-500/40 bg-emerald-950/20',
    };
  } else if (fib4 <= 2.67) {
    return {
      category: 'Indeterminate',
      description: 'FIB-4 1.30–2.67: Indeterminate zone. Clinical guidelines (AASLD/EASL) recommend secondary non-invasive testing (e.g. VCTE elastography).',
      colorClass: 'text-amber-300 border-amber-500/40 bg-amber-950/20',
    };
  } else {
    return {
      category: 'High Risk',
      description: 'FIB-4 > 2.67: High specificity for advanced fibrosis (Metavir F3–F4); clinical hepatology referral typically indicated.',
      colorClass: 'text-rose-400 border-rose-500/40 bg-rose-950/20',
    };
  }
}
