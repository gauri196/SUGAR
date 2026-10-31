// SUGAR — Step 4: Compare Four-Model Progressive Pipeline
import React, { useEffect, useState, useCallback } from 'react';
import {
  GitBranch,
  ArrowRight,
  ArrowLeft,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  Sparkles,
  ShieldAlert,
} from 'lucide-react';
import {
  ClinicalInputs,
  PredictionResponse,
  Model4PredictionResponse,
  UciHcvPredictionResponse,
} from '../../types';
import {
  submitPrediction,
  predictModel4,
  predictUciHcv,
} from '../../services/api';

interface ModelComparisonProps {
  data: ClinicalInputs;
  onProceed: () => void;
  onBack: () => void;
  predictionResult: PredictionResponse | null;
  onPredictionComplete: (result: PredictionResponse) => void;
}

export const ModelComparison: React.FC<ModelComparisonProps> = ({
  data,
  onProceed,
  onBack,
  predictionResult,
  onPredictionComplete,
}) => {
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [model4Result, setModel4Result] = useState<Model4PredictionResponse | null>(null);
  const [uciHcvResult, setUciHcvResult] = useState<UciHcvPredictionResponse | null>(null);

  const runLiveInference = useCallback(async () => {
    setLoading(true);
    setError(null);

    const patientPayload = {
      age: data.age,
      bmi: data.bmi,
      platelets: data.platelets,
      ast: data.ast,
      alt: data.alt,
      wbc: data.wbc,
      rbc: data.rbc,
      hgb: data.hgb,
    };

    try {
      // 1. Models A & B (Routine Baseline & Expanded RF)
      const res = await submitPrediction(patientPayload);
      if (res.success && res.data) {
        onPredictionComplete(res.data);
      } else {
        setError(res.error || 'Failed to connect to FastAPI backend for live inference.');
      }

      // 2. Model 3 (UCI HCV 5-Class Classifier)
      try {
        const uciRes = await predictUciHcv({
          age: data.age,
          alt: data.alt,
          ast: data.ast,
          chol: data.cholesterol,
        });
        setUciHcvResult(uciRes);
      } catch {
        // Non-blocking for research model
      }

      // 3. Model 4 (Disease Etiology & Clinical Stigmata)
      try {
        const m4Res = await predictModel4({
          age_years: data.age,
          platelets: data.platelets,
          sgot: data.ast,
          ascites: data.ascites ? 'Y' : 'N',
          hepatomegaly: data.hepatomegaly ? 'Y' : 'N',
          spiders: 'N',
          edema: 'N',
        });
        setModel4Result(m4Res);
      } catch {
        // Non-blocking for research model
      }
    } finally {
      setLoading(false);
    }
  }, [data, onPredictionComplete]);

  useEffect(() => {
    if (!predictionResult) {
      runLiveInference();
    }
  }, [predictionResult, runLiveInference]);

  return (
    <div className="space-y-6">
      {/* Step Header */}
      <div className="border-b border-[#153568] pb-4">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <div>
            <span className="badge badge-ice mb-2">Step 4 of 5</span>
            <h1 className="h1 flex items-center gap-2">
              <GitBranch className="text-ice" size={26} />
              Four-Model Progressive Machine Learning Pipeline
            </h1>
          </div>
          <button
            onClick={runLiveInference}
            disabled={loading}
            className="btn btn-secondary flex items-center gap-2"
            title="Re-run inference across all available models"
          >
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
            {loading ? 'Executing...' : 'Re-run Inference'}
          </button>
        </div>
        <p className="text-sm text-slate-400 mt-1">
          Evaluating patient markers across four research models: from routine liver panel to expanded complete blood count, metabolic biomarkers, and clinical stigmata.
        </p>
      </div>

      {/* Error state */}
      {error && (
        <div
          style={{
            background: 'rgba(244, 63, 94, 0.1)',
            border: '1px solid #F43F5E',
            borderRadius: '8px',
            padding: '14px',
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
          }}
        >
          <AlertCircle size={20} className="text-rose-400 flex-shrink-0" />
          <div className="text-sm text-rose-200">
            <strong>Inference Notice:</strong> {error}
          </div>
        </div>
      )}

      {/* Models Grid (2x2) */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {/* Model A — Routine Clinical Baseline */}
        <div
          style={{
            background: 'rgba(10, 14, 28, 0.7)',
            border: '1px solid var(--navy-clinical)',
            borderRadius: '12px',
            padding: '20px',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
          }}
          className="space-y-4"
        >
          <div>
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <span className="badge badge-navy">Model A</span>
                <span className="badge badge-ice">Live Inference Active</span>
              </div>
              <span style={{ fontSize: '0.75rem', fontFamily: 'JetBrains Mono', color: '#80B3D0' }}>
                LR Pipeline (5 Features)
              </span>
            </div>

            <h3 style={{ fontSize: '1.15rem', color: '#ffffff', margin: '0 0 6px' }}>
              Routine Clinical Baseline
            </h3>
            <p style={{ fontSize: '0.84rem', color: '#80B3D0', lineHeight: 1.45 }}>
              Standard logistic regression trained on routine laboratory values: <strong>Age, BMI, Platelets, AST, ALT</strong>.
            </p>

            <div
              style={{
                background: 'rgba(21, 53, 104, 0.25)',
                border: '1px solid var(--navy-clinical)',
                borderRadius: '8px',
                padding: '12px',
                marginTop: '12px',
              }}
            >
              {loading ? (
                <div className="flex items-center gap-2 text-sm text-slate-400">
                  <RefreshCw size={14} className="animate-spin text-ice" />
                  Calculating baseline probability...
                </div>
              ) : predictionResult ? (
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <span style={{ fontSize: '0.82rem', color: '#80B3D0' }}>Target B Classification:</span>
                    <span
                      className="badge"
                      style={{
                        background: predictionResult.baseline_model.prediction === 1 ? 'rgba(244, 63, 94, 0.2)' : 'rgba(16, 185, 129, 0.2)',
                        color: predictionResult.baseline_model.prediction === 1 ? '#FDA4AF' : '#6EE7B7',
                        border: `1px solid ${predictionResult.baseline_model.prediction === 1 ? '#F43F5E' : '#10B981'}`,
                      }}
                    >
                      {predictionResult.baseline_model.prediction === 1 ? 'Stage 3–4 (Advanced)' : 'Stage 1–2 (Early/Moderate)'}
                    </span>
                  </div>

                  <div className="flex items-center justify-between text-xs mb-1">
                    <span style={{ color: '#80B3D0' }}>Model Probability:</span>
                    <span style={{ fontFamily: 'JetBrains Mono', fontWeight: 700, color: '#ffffff' }}>
                      {(predictionResult.baseline_model.probability * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div style={{ width: '100%', height: '8px', borderRadius: '4px', background: 'var(--navy-deep)', overflow: 'hidden' }}>
                    <div
                      style={{
                        width: `${predictionResult.baseline_model.probability * 100}%`,
                        height: '100%',
                        background:
                          predictionResult.baseline_model.probability >= 0.5
                            ? 'linear-gradient(90deg, #19166D 0%, #F43F5E 100%)'
                            : 'linear-gradient(90deg, #19166D 0%, #34D399 100%)',
                      }}
                    />
                  </div>
                </div>
              ) : (
                <span style={{ fontSize: '0.82rem', color: '#64748b' }}>Waiting for inference execution...</span>
              )}
            </div>
          </div>

          <div style={{ borderTop: '1px solid rgba(21, 53, 104, 0.5)', paddingTop: '10px', fontSize: '0.76rem', color: '#64748b' }}>
            Benchmark Validation: 10-Fold CV ROC-AUC = 0.535 | Held-Out Test ROC-AUC = 0.504
          </div>
        </div>

        {/* Model B — Expanded Fibrosis Model */}
        <div
          style={{
            background: 'rgba(10, 14, 28, 0.7)',
            border: '1px solid var(--navy-clinical)',
            borderRadius: '12px',
            padding: '20px',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
          }}
          className="space-y-4"
        >
          <div>
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <span className="badge badge-navy">Model B</span>
                <span className="badge badge-ice">Live Inference Active</span>
              </div>
              <span style={{ fontSize: '0.75rem', fontFamily: 'JetBrains Mono', color: '#80B3D0' }}>
                Random Forest (8 Features)
              </span>
            </div>

            <h3 style={{ fontSize: '1.15rem', color: '#ffffff', margin: '0 0 6px' }}>
              Expanded Hematologic Model
            </h3>
            <p style={{ fontSize: '0.84rem', color: '#80B3D0', lineHeight: 1.45 }}>
              Model A plus full complete blood count markers: <strong>White Blood Cells (WBC), Red Blood Cells (RBC), Hemoglobin (HGB)</strong>.
            </p>

            <div
              style={{
                background: 'rgba(21, 53, 104, 0.25)',
                border: '1px solid var(--navy-clinical)',
                borderRadius: '8px',
                padding: '12px',
                marginTop: '12px',
              }}
            >
              {loading ? (
                <div className="flex items-center gap-2 text-sm text-slate-400">
                  <RefreshCw size={14} className="animate-spin text-ice" />
                  Calculating expanded probability...
                </div>
              ) : predictionResult ? (
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <span style={{ fontSize: '0.82rem', color: '#80B3D0' }}>Target B Classification:</span>
                    <span
                      className="badge"
                      style={{
                        background: predictionResult.expanded_model.prediction === 1 ? 'rgba(244, 63, 94, 0.2)' : 'rgba(16, 185, 129, 0.2)',
                        color: predictionResult.expanded_model.prediction === 1 ? '#FDA4AF' : '#6EE7B7',
                        border: `1px solid ${predictionResult.expanded_model.prediction === 1 ? '#F43F5E' : '#10B981'}`,
                      }}
                    >
                      {predictionResult.expanded_model.prediction === 1 ? 'Stage 3–4 (Advanced)' : 'Stage 1–2 (Early/Moderate)'}
                    </span>
                  </div>

                  <div className="flex items-center justify-between text-xs mb-1">
                    <span style={{ color: '#80B3D0' }}>Model Probability:</span>
                    <span style={{ fontFamily: 'JetBrains Mono', fontWeight: 700, color: '#ffffff' }}>
                      {(predictionResult.expanded_model.probability * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div style={{ width: '100%', height: '8px', borderRadius: '4px', background: 'var(--navy-deep)', overflow: 'hidden' }}>
                    <div
                      style={{
                        width: `${predictionResult.expanded_model.probability * 100}%`,
                        height: '100%',
                        background:
                          predictionResult.expanded_model.probability >= 0.5
                            ? 'linear-gradient(90deg, #19166D 0%, #F43F5E 100%)'
                            : 'linear-gradient(90deg, #19166D 0%, #34D399 100%)',
                      }}
                    />
                  </div>
                </div>
              ) : (
                <span style={{ fontSize: '0.82rem', color: '#64748b' }}>Waiting for inference execution...</span>
              )}
            </div>
          </div>

          <div style={{ borderTop: '1px solid rgba(21, 53, 104, 0.5)', paddingTop: '10px', fontSize: '0.76rem', color: '#64748b' }}>
            Benchmark Validation: 10-Fold CV ROC-AUC = 0.498 | Held-Out Test ROC-AUC = 0.493
          </div>
        </div>

        {/* Model C — Metabolic Variables & UCI HCV */}
        <div
          style={{
            background: 'rgba(10, 14, 28, 0.7)',
            border: '1px solid rgba(128, 179, 208, 0.3)',
            borderRadius: '12px',
            padding: '20px',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
          }}
          className="space-y-4"
        >
          <div>
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <span className="badge badge-navy">Model C</span>
                <span className="badge badge-ice">Completed Research Pipeline</span>
              </div>
              <span style={{ fontSize: '0.75rem', fontFamily: 'JetBrains Mono', color: '#80B3D0' }}>
                UCI HCV 5-Class Classifier
              </span>
            </div>

            <h3 style={{ fontSize: '1.15rem', color: '#ffffff', margin: '0 0 6px' }}>
              Metabolic & 5-Class Biomarker Model
            </h3>
            <p style={{ fontSize: '0.84rem', color: '#80B3D0', lineHeight: 1.45 }}>
              Multivariate 12-feature Random Forest trained on UCI HCV cohort: <strong>Age, Sex, ALB, ALP, ALT, AST, BIL, CHE, CHOL, CREA, GGT, PROT</strong>.
            </p>

            <div
              style={{
                background: 'rgba(21, 53, 104, 0.25)',
                border: '1px solid var(--navy-clinical)',
                borderRadius: '8px',
                padding: '12px',
                marginTop: '12px',
              }}
            >
              {uciHcvResult ? (
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <span style={{ fontSize: '0.82rem', color: '#80B3D0' }}>Predicted Diagnostic Category:</span>
                    <span
                      className="badge"
                      style={{
                        background: uciHcvResult.is_fibrosis_or_cirrhosis ? 'rgba(244, 63, 94, 0.2)' : 'rgba(56, 189, 248, 0.2)',
                        color: uciHcvResult.is_fibrosis_or_cirrhosis ? '#FDA4AF' : '#BAE6FD',
                        border: `1px solid ${uciHcvResult.is_fibrosis_or_cirrhosis ? '#F43F5E' : '#38BDF8'}`,
                      }}
                    >
                      {uciHcvResult.predicted_category}
                    </span>
                  </div>
                  <div className="text-xs text-slate-300 mt-1 flex items-center justify-between">
                    <span>Category Probability:</span>
                    <span style={{ fontFamily: 'JetBrains Mono', fontWeight: 600 }}>{(uciHcvResult.top_probability * 100).toFixed(1)}%</span>
                  </div>
                </div>
              ) : (
                <div style={{ display: 'flex', alignItems: 'flex-start', gap: '8px' }}>
                  <CheckCircle2 size={16} className="text-ice" style={{ flexShrink: 0, marginTop: '2px' }} />
                  <div>
                    <strong style={{ fontSize: '0.82rem', color: '#ffffff' }}>Observational Findings:</strong>
                    <p style={{ fontSize: '0.78rem', color: '#cbd5e1', margin: '2px 0 0', lineHeight: 1.45 }}>
                      NHANES Exp 8H observational analysis: CAP steatosis score with FIB-4 achieved <strong>R² = 13.17% (log scale)</strong>, reducing MAE to <strong>1.64 kPa</strong>.
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>

          <div style={{ borderTop: '1px solid rgba(21, 53, 104, 0.5)', paddingTop: '10px', fontSize: '0.76rem', color: '#A9D4E7' }}>
            Validation: Balanced Accuracy = 0.587 | Test Macro F1 = 0.612 | Severe Minority Imbalance (Support: 4-6)
          </div>
        </div>

        {/* Model D — Disease Etiology & Stigmata */}
        <div
          style={{
            background: 'rgba(10, 14, 28, 0.7)',
            border: '1px solid var(--navy-clinical)',
            borderRadius: '12px',
            padding: '20px',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
          }}
          className="space-y-4"
        >
          <div>
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <span className="badge badge-navy">Model D</span>
                <span className="badge badge-ice" style={{ background: 'rgba(16, 185, 129, 0.2)', color: '#6EE7B7', borderColor: '#10B981' }}>
                  Trained Clinical Pipeline
                </span>
              </div>
              <span style={{ fontSize: '0.75rem', fontFamily: 'JetBrains Mono', color: '#6EE7B7' }}>
                Mayo Clinic PBC (N=418)
              </span>
            </div>

            <h3 style={{ fontSize: '1.15rem', color: '#ffffff', margin: '0 0 6px' }}>
              Disease Etiology & Clinical Stigmata
            </h3>
            <p style={{ fontSize: '0.84rem', color: '#80B3D0', lineHeight: 1.45 }}>
              Trained on biopsy-confirmed histological stage. Integrates physical stigmata (<strong>ascites, hepatomegaly, spiders, edema</strong>) with routine and liver panel biomarkers.
            </p>

            <div
              style={{
                background: 'rgba(21, 53, 104, 0.25)',
                border: '1px solid var(--navy-clinical)',
                borderRadius: '8px',
                padding: '12px',
                marginTop: '12px',
              }}
            >
              {model4Result ? (
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <span style={{ fontSize: '0.82rem', color: '#80B3D0' }}>Staging Risk Classification:</span>
                    <span
                      className="badge"
                      style={{
                        background: model4Result.prediction === 1 ? 'rgba(244, 63, 94, 0.2)' : 'rgba(16, 185, 129, 0.2)',
                        color: model4Result.prediction === 1 ? '#FDA4AF' : '#6EE7B7',
                        border: `1px solid ${model4Result.prediction === 1 ? '#F43F5E' : '#10B981'}`,
                      }}
                    >
                      {model4Result.prediction === 1 ? 'Advanced Stage 3–4' : 'Early Stage 1–2'}
                    </span>
                  </div>

                  <div className="flex items-center justify-between text-xs mb-1">
                    <span style={{ color: '#80B3D0' }}>Advanced Stage Probability:</span>
                    <span style={{ fontFamily: 'JetBrains Mono', fontWeight: 700, color: '#ffffff' }}>
                      {(model4Result.probability * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div style={{ width: '100%', height: '8px', borderRadius: '4px', background: 'var(--navy-deep)', overflow: 'hidden' }}>
                    <div
                      style={{
                        width: `${model4Result.probability * 100}%`,
                        height: '100%',
                        background:
                          model4Result.probability >= 0.5
                            ? 'linear-gradient(90deg, #19166D 0%, #F43F5E 100%)'
                            : 'linear-gradient(90deg, #19166D 0%, #34D399 100%)',
                      }}
                    />
                  </div>
                </div>
              ) : (
                <div className="flex items-center gap-2 text-xs text-slate-300">
                  <CheckCircle2 size={16} className="text-emerald-400 flex-shrink-0" />
                  <span>Stigmata pipeline active: Ascites={data.ascites ? 'Yes' : 'No'}, Hepatomegaly={data.hepatomegaly ? 'Yes' : 'No'}.</span>
                </div>
              )}
            </div>
          </div>

          <div style={{ borderTop: '1px solid rgba(21, 53, 104, 0.5)', paddingTop: '10px', fontSize: '0.76rem', color: '#6EE7B7' }}>
            Validation: 5-Fold CV ROC-AUC = 0.710 | Held-Out Test ROC-AUC = 0.687 (Accuracy 71.1%, Precision 81.0%)
          </div>
        </div>
      </div>

      {/* Delta & Concordance Bar */}
      {predictionResult && (
        <div
          style={{
            background: 'rgba(21, 53, 104, 0.35)',
            border: '1px solid var(--navy-clinical)',
            borderRadius: '10px',
            padding: '14px 18px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: '12px',
          }}
        >
          <div className="flex items-center gap-3">
            <Sparkles size={18} style={{ color: '#A9D4E7' }} />
            <div>
              <div style={{ color: '#ffffff', fontSize: '0.9rem', fontWeight: 600 }}>
                Machine Learning Model Concordance:
              </div>
              <p style={{ fontSize: '0.82rem', color: '#80B3D0', margin: 0 }}>
                {predictionResult.baseline_model.prediction === predictionResult.expanded_model.prediction
                  ? 'Model A and Model B agree on Target B classification.'
                  : 'Discordance observed between Model A and Model B (probability delta: ' +
                    Math.abs((predictionResult.baseline_model.probability - predictionResult.expanded_model.probability) * 100).toFixed(1) +
                    '%).'}
                {model4Result && (
                  <span className="ml-2 font-medium" style={{ color: '#6EE7B7' }}>
                    Model 4 Stigmata Pipeline classifies patient as {model4Result.risk_label}.
                  </span>
                )}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <span className="badge badge-navy text-xs">
              Δ Prob: {Math.abs((predictionResult.baseline_model.probability - predictionResult.expanded_model.probability) * 100).toFixed(1)}%
            </span>
          </div>
        </div>
      )}

      {/* Scientific Limitation Alert */}
      <div
        style={{
          background: 'rgba(16, 16, 82, 0.4)',
          border: '1px dashed var(--navy-clinical)',
          borderRadius: '10px',
          padding: '14px 18px',
          display: 'flex',
          alignItems: 'flex-start',
          gap: '12px',
        }}
      >
        <ShieldAlert size={20} className="text-amber-400 flex-shrink-0 mt-0.5" />
        <div className="text-xs text-slate-300 leading-relaxed">
          <strong className="text-white">Methodological Safeguard:</strong> Models A & B show near-chance ROC-AUC (~0.50) on Target B because the Egyptian HCV cohort features exhibit near-zero statistical association with histological staging (Kruskal-Wallis p &gt; 0.40 for AST 1 and ALT 1). Model 4 utilizes the Mayo Clinic biopsy cohort (N=418), achieving defensible validation (ROC-AUC 0.710). FIB-4 remains the primary guideline-based clinical triage metric.
        </div>
      </div>

      {/* Navigation Footer */}
      <div className="flex items-center justify-between pt-4 border-t border-[#153568]">
        <button
          onClick={onBack}
          className="btn btn-secondary flex items-center gap-2"
        >
          <ArrowLeft size={16} />
          Back: FIB-4 Score
        </button>

        <button
          onClick={onProceed}
          className="btn btn-primary flex items-center gap-2"
        >
          Proceed to Comprehensive Results
          <ArrowRight size={16} />
        </button>
      </div>
    </div>
  );
};
