// SUGAR — Polished Risk Stratification Lab (Dual Model Inference & Real-Time FIB-4 Index)
import React, { useState } from 'react';
import {
  Activity,
  Calculator,
  Send,
  RefreshCw,
  Sliders,
  ShieldAlert,
  Sparkles,
  Info,
} from 'lucide-react';
import { PatientData, PredictionResponse } from '../../types';
import {
  submitPrediction,
  calculateFib4,
  interpretFib4,
} from '../../services/api';

const PRESETS: { label: string; description: string; data: PatientData }[] = [
  {
    label: 'Profile A: Routine Low Risk',
    description: '42yo adult, normal platelets & transaminases, normal BMI.',
    data: {
      age: 42,
      bmi: 24.5,
      platelets: 255,
      ast: 25,
      alt: 24,
      wbc: 6.5,
      rbc: 4.8,
      hgb: 15.0,
    },
  },
  {
    label: 'Profile B: Indeterminate Zone',
    description: '56yo with mild thrombocytopenia (145k) and moderately elevated enzymes.',
    data: {
      age: 56,
      bmi: 29.4,
      platelets: 145,
      ast: 58,
      alt: 48,
      wbc: 8.2,
      rbc: 4.3,
      hgb: 13.6,
    },
  },
  {
    label: 'Profile C: Elevated Risk Cohort',
    description: '64yo with marked thrombocytopenia (92k), high transaminase ratio, leukocytosis.',
    data: {
      age: 64,
      bmi: 32.8,
      platelets: 92,
      ast: 98,
      alt: 65,
      wbc: 10.4,
      rbc: 3.9,
      hgb: 12.1,
    },
  },
];

export const RiskLab: React.FC = () => {
  const [patient, setPatient] = useState<PatientData>(PRESETS[0].data);
  const [loading, setLoading] = useState<boolean>(false);
  const [predictionResult, setPredictionResult] = useState<{
    data: PredictionResponse;
    source: 'live' | 'fallback';
  } | null>(null);

  const fib4Score = calculateFib4(
    patient.age,
    patient.ast,
    patient.alt,
    patient.platelets
  );
  const fib4Interpretation = interpretFib4(fib4Score);

  const handleInputChange = (field: keyof PatientData, value: number) => {
    setPatient((prev) => ({
      ...prev,
      [field]: isNaN(value) ? 0 : value,
    }));
  };

  const handlePredict = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setLoading(true);

    const res = await submitPrediction(patient);
    setLoading(false);

    if (res.success) {
      setPredictionResult({
        data: res.data,
        source: res.source,
      });
    }
  };

  const loadPreset = (preset: (typeof PRESETS)[0]) => {
    setPatient(preset.data);
    setPredictionResult(null);
  };

  return (
    <div className="space-y-6">
      {/* Lab Header */}
      <div className="flex items-center justify-between flex-wrap gap-4 pb-3 border-b border-[#153568]">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="h1 flex items-center gap-2">
              <Activity className="text-ice" size={26} />
              Risk Stratification Lab
            </h1>
            <span className="badge badge-ice">Dual Model Inference</span>
          </div>
          <p className="text-muted mt-1" style={{ fontSize: '0.92rem' }}>
            FastAPI-powered prediction comparing <strong>Routine Clinical Baseline (Logistic Regression)</strong> vs. <strong>Expanded Random Forest</strong>.
          </p>
        </div>

        {/* Preset Selector */}
        <div className="flex items-center gap-2">
          <span style={{ fontSize: '0.85rem', color: '#80B3D0' }}>Presets:</span>
          {PRESETS.map((p, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => loadPreset(p)}
              className="btn btn-secondary"
              style={{ padding: '6px 12px', fontSize: '0.82rem' }}
              title={p.description}
            >
              Profile {String.fromCharCode(65 + idx)}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-12 gap-6">
        {/* Left Column: Parameter Input Panel */}
        <div className="col-span-7 space-y-4">
          <form onSubmit={handlePredict} className="sugar-card space-y-5">
            <div className="card-header flex items-center justify-between">
              <h2 className="h2 flex items-center gap-2" style={{ fontSize: '1.15rem' }}>
                <Sliders size={18} style={{ color: '#A9D4E7' }} />
                <span>Laboratory Biomarker Inputs</span>
              </h2>
              <span className="badge badge-navy">8 Clinical Variables</span>
            </div>

            {/* Inputs in 2 Columns */}
            <div className="grid grid-2 gap-4">
              {/* Age */}
              <div className="input-row">
                <div className="input-label-bar">
                  <span>Age (years)</span>
                  <span className="val-badge">{patient.age}</span>
                </div>
                <input
                  type="range"
                  min="18"
                  max="85"
                  step="1"
                  value={patient.age}
                  onChange={(e) => handleInputChange('age', parseFloat(e.target.value))}
                />
              </div>

              {/* BMI */}
              <div className="input-row">
                <div className="input-label-bar">
                  <span>BMI (kg/m²)</span>
                  <span className="val-badge">{patient.bmi.toFixed(1)}</span>
                </div>
                <input
                  type="range"
                  min="16"
                  max="45"
                  step="0.1"
                  value={patient.bmi}
                  onChange={(e) => handleInputChange('bmi', parseFloat(e.target.value))}
                />
              </div>

              {/* Platelets */}
              <div className="input-row">
                <div className="input-label-bar">
                  <span>Platelet Count (10³/μL)</span>
                  <span className="val-badge">{patient.platelets}</span>
                </div>
                <input
                  type="range"
                  min="30"
                  max="500"
                  step="1"
                  value={patient.platelets}
                  onChange={(e) =>
                    handleInputChange('platelets', parseFloat(e.target.value))
                  }
                />
              </div>

              {/* AST 1 */}
              <div className="input-row">
                <div className="input-label-bar">
                  <span>AST 1 (Units / Ratio)</span>
                  <span className="val-badge">{patient.ast}</span>
                </div>
                <input
                  type="range"
                  min="5"
                  max="200"
                  step="1"
                  value={patient.ast}
                  onChange={(e) => handleInputChange('ast', parseFloat(e.target.value))}
                />
              </div>

              {/* ALT 1 */}
              <div className="input-row">
                <div className="input-label-bar">
                  <span>ALT 1 (Units / Ratio)</span>
                  <span className="val-badge">{patient.alt}</span>
                </div>
                <input
                  type="range"
                  min="5"
                  max="200"
                  step="1"
                  value={patient.alt}
                  onChange={(e) => handleInputChange('alt', parseFloat(e.target.value))}
                />
              </div>

              {/* WBC */}
              <div className="input-row">
                <div className="input-label-bar">
                  <span>WBC (10³/μL) [Expanded]</span>
                  <span className="val-badge">{patient.wbc.toFixed(1)}</span>
                </div>
                <input
                  type="range"
                  min="2"
                  max="20"
                  step="0.1"
                  value={patient.wbc}
                  onChange={(e) => handleInputChange('wbc', parseFloat(e.target.value))}
                />
              </div>

              {/* RBC */}
              <div className="input-row">
                <div className="input-label-bar">
                  <span>RBC (10⁶/μL) [Expanded]</span>
                  <span className="val-badge">{patient.rbc.toFixed(2)}</span>
                </div>
                <input
                  type="range"
                  min="2.5"
                  max="7.0"
                  step="0.05"
                  value={patient.rbc}
                  onChange={(e) => handleInputChange('rbc', parseFloat(e.target.value))}
                />
              </div>

              {/* HGB */}
              <div className="input-row">
                <div className="input-label-bar">
                  <span>Hemoglobin (g/dL) [Expanded]</span>
                  <span className="val-badge">{patient.hgb.toFixed(1)}</span>
                </div>
                <input
                  type="range"
                  min="7.0"
                  max="19.0"
                  step="0.1"
                  value={patient.hgb}
                  onChange={(e) => handleInputChange('hgb', parseFloat(e.target.value))}
                />
              </div>
            </div>

            {/* Scientific Caveat */}
            <div
              style={{
                background: 'rgba(16, 16, 82, 0.5)',
                border: '1px solid var(--navy-clinical)',
                borderRadius: '8px',
                padding: '12px 16px',
                fontSize: '0.84rem',
                color: '#cbd5e1',
                display: 'flex',
                gap: '10px',
                alignItems: 'flex-start',
              }}
            >
              <Info size={16} style={{ color: '#A9D4E7', flexShrink: 0, marginTop: '2px' }} />
              <p style={{ margin: 0, fontSize: '0.84rem', lineHeight: '1.45' }}>
                <strong>Scientific Integrity Note:</strong> In the training Egyptian HCV cohort,{' '}
                <code className="text-ice">AST 1</code> and{' '}
                <code className="text-ice">ALT 1</code> are dataset-specific ratio features rather than raw international U/L values. Models represent exploratory machine learning benchmarking.
              </p>
            </div>

            {/* Actions */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: '8px' }}>
              <button
                type="button"
                onClick={() => loadPreset(PRESETS[0])}
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: '#80B3D0',
                  fontSize: '0.86rem',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                }}
              >
                <RefreshCw size={14} />
                <span>Reset to Profile A</span>
              </button>

              <button
                type="submit"
                disabled={loading}
                className="btn btn-primary"
                style={{ padding: '10px 22px' }}
              >
                {loading ? (
                  <>
                    <RefreshCw size={16} className="animate-spin" />
                    <span>Querying Backend...</span>
                  </>
                ) : (
                  <>
                    <Send size={16} />
                    <span>Execute Model Inference</span>
                  </>
                )}
              </button>
            </div>
          </form>

          {/* Real-Time FIB-4 Index Card */}
          <div className="sugar-card space-y-3">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Calculator size={18} style={{ color: '#A9D4E7' }} />
                <h3 style={{ fontSize: '1.05rem', color: '#ffffff', margin: 0 }}>
                  Clinical FIB-4 Index Calculation
                </h3>
              </div>
              <span
                style={{
                  fontFamily: 'JetBrains Mono',
                  fontSize: '1.15rem',
                  fontWeight: 700,
                  color: '#ffffff',
                  background: 'var(--navy-royal)',
                  border: '1px solid var(--ice-blue)',
                  padding: '4px 12px',
                  borderRadius: '6px',
                }}
              >
                FIB-4 = {fib4Score}
              </span>
            </div>

            <div
              style={{
                borderRadius: '8px',
                padding: '12px 16px',
                border: '1px solid',
              }}
              className={fib4Interpretation.colorClass}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                <strong style={{ fontSize: '0.95rem' }}>Classification: {fib4Interpretation.category}</strong>
                <span style={{ fontFamily: 'JetBrains Mono', fontSize: '0.8rem' }}>
                  Formula: (Age × AST) / (Plat × √ALT)
                </span>
              </div>
              <p style={{ fontSize: '0.86rem', margin: 0, lineHeight: '1.45' }}>
                {fib4Interpretation.description}
              </p>
            </div>
          </div>
        </div>

        {/* Right Column: Model Inference Outputs */}
        <div className="col-span-5 space-y-4">
          <div className="sugar-card-elevated space-y-5" style={{ minHeight: '480px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
            <div>
              <div className="card-header flex items-center justify-between">
                <h2 className="h2 flex items-center gap-2" style={{ fontSize: '1.15rem' }}>
                  <Sparkles size={18} style={{ color: '#A9D4E7' }} />
                  <span>Dual Model Output</span>
                </h2>
                {predictionResult && (
                  <span
                    className={`badge ${
                      predictionResult.source === 'live' ? 'badge-success' : 'badge-warning'
                    }`}
                  >
                    {predictionResult.source === 'live' ? 'FastAPI Live' : 'Validated Fallback'}
                  </span>
                )}
              </div>

              {!predictionResult && !loading && (
                <div style={{ textAlign: 'center', padding: '48px 16px', color: '#80B3D0' }}>
                  <Activity size={40} style={{ margin: '0 auto 16px', color: '#153568' }} />
                  <p style={{ fontSize: '0.92rem' }}>
                    Adjust patient inputs on the left and click <strong>Execute Model Inference</strong> to compare predictions.
                  </p>
                </div>
              )}

              {loading && (
                <div style={{ textAlign: 'center', padding: '56px 16px', color: '#A9D4E7' }}>
                  <RefreshCw size={36} className="animate-spin" style={{ margin: '0 auto 16px' }} />
                  <p style={{ fontFamily: 'JetBrains Mono', fontSize: '0.9rem' }}>
                    Computing scikit-learn model inference...
                  </p>
                </div>
              )}

              {predictionResult && (
                <div className="space-y-4" style={{ marginTop: '12px' }}>
                  {/* Model 1: Baseline */}
                  <div
                    style={{
                      background: 'rgba(10, 14, 28, 0.85)',
                      border: '1px solid var(--navy-clinical)',
                      borderRadius: '8px',
                      padding: '16px',
                    }}
                    className="space-y-3"
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div>
                        <h4 style={{ color: '#ffffff', fontSize: '0.95rem', margin: 0 }}>
                          1. Routine Clinical Baseline
                        </h4>
                        <span style={{ fontSize: '0.78rem', color: '#80B3D0' }}>
                          Logistic Regression (5 Features)
                        </span>
                      </div>
                      <span
                        className={`badge ${
                          predictionResult.data.baseline_model.prediction === 1
                            ? 'badge-danger'
                            : 'badge-success'
                        }`}
                      >
                        {predictionResult.data.baseline_model.prediction === 1
                          ? 'Elevated Risk (Class 1)'
                          : 'Low Risk (Class 0)'}
                      </span>
                    </div>

                    <div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: '6px' }}>
                        <span style={{ color: '#80B3D0' }}>Elevated Risk Probability:</span>
                        <span style={{ fontFamily: 'JetBrains Mono', fontWeight: 700, color: '#ffffff' }}>
                          {(predictionResult.data.baseline_model.probability * 100).toFixed(1)}%
                        </span>
                      </div>
                      <div style={{ width: '100%', height: '8px', borderRadius: '4px', background: 'var(--navy-deep)', overflow: 'hidden' }}>
                        <div
                          style={{
                            width: `${predictionResult.data.baseline_model.probability * 100}%`,
                            height: '100%',
                            background:
                              predictionResult.data.baseline_model.probability >= 0.5
                                ? 'linear-gradient(90deg, #153568 0%, #EF4444 100%)'
                                : 'linear-gradient(90deg, #153568 0%, #10B981 100%)',
                            transition: 'width 0.4s ease',
                          }}
                        />
                      </div>
                    </div>
                  </div>

                  {/* Model 2: Expanded */}
                  <div
                    style={{
                      background: 'rgba(10, 14, 28, 0.85)',
                      border: '1px solid var(--border-active)',
                      borderRadius: '8px',
                      padding: '16px',
                    }}
                    className="space-y-3"
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div>
                        <h4 style={{ color: '#A9D4E7', fontSize: '0.95rem', margin: 0 }}>
                          2. Expanded Fibrosis Model
                        </h4>
                        <span style={{ fontSize: '0.78rem', color: '#80B3D0' }}>
                          Random Forest (8 Features: + WBC, RBC, HGB)
                        </span>
                      </div>
                      <span
                        className={`badge ${
                          predictionResult.data.expanded_model.prediction === 1
                            ? 'badge-danger'
                            : 'badge-success'
                        }`}
                      >
                        {predictionResult.data.expanded_model.prediction === 1
                          ? 'Elevated Risk (Class 1)'
                          : 'Low Risk (Class 0)'}
                      </span>
                    </div>

                    <div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: '6px' }}>
                        <span style={{ color: '#80B3D0' }}>Elevated Risk Probability:</span>
                        <span style={{ fontFamily: 'JetBrains Mono', fontWeight: 700, color: '#ffffff' }}>
                          {(predictionResult.data.expanded_model.probability * 100).toFixed(1)}%
                        </span>
                      </div>
                      <div style={{ width: '100%', height: '8px', borderRadius: '4px', background: 'var(--navy-deep)', overflow: 'hidden' }}>
                        <div
                          style={{
                            width: `${predictionResult.data.expanded_model.probability * 100}%`,
                            height: '100%',
                            background:
                              predictionResult.data.expanded_model.probability >= 0.5
                                ? 'linear-gradient(90deg, #19166D 0%, #F43F5E 100%)'
                                : 'linear-gradient(90deg, #19166D 0%, #34D399 100%)',
                            transition: 'width 0.4s ease',
                          }}
                        />
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Disclaimer */}
            <div style={{ borderTop: '1px solid var(--navy-clinical)', paddingTop: '12px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#FBBF24', fontSize: '0.82rem', fontWeight: 600, marginBottom: '4px' }}>
                <ShieldAlert size={14} />
                <span>Strict Research Use Only</span>
              </div>
              <p style={{ fontSize: '0.8rem', color: '#80B3D0', margin: 0, lineHeight: '1.45' }}>
                {predictionResult?.data?.disclaimer ||
                  'Research prototype for educational exploration. It does not provide medical diagnoses or replace clinical staging.'}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
