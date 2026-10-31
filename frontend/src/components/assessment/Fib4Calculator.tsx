// SUGAR — Step 3: Clinical FIB-4 Index Calculation & Risk Stratification
import React, { useState, useEffect, useRef } from 'react';
import {
  Calculator,
  ArrowRight,
  ArrowLeft,
  AlertTriangle,
  Info,
  CheckCircle2,
  HelpCircle,
  FileText,
  Loader2,
  Database,
} from 'lucide-react';
import { ClinicalInputs, AssessmentDetailResponse } from '../../types';
import { calculateFib4, interpretFib4, createAssessment } from '../../services/api';

interface Fib4CalculatorProps {
  data: ClinicalInputs;
  onProceed: () => void;
  onBack: () => void;
  onAssessmentCreated?: (assessmentId: string) => void;
}

export const Fib4Calculator: React.FC<Fib4CalculatorProps> = ({
  data,
  onProceed,
  onBack,
  onAssessmentCreated,
}) => {
  const [assessment, setAssessment] = useState<AssessmentDetailResponse | null>(null);
  const [isPersisting, setIsPersisting] = useState<boolean>(false);
  const [persistError, setPersistError] = useState<string | null>(null);
  const hasTriggeredRef = useRef<boolean>(false);

  // Fallback / reactive computation
  const localScore = calculateFib4(data.age, data.ast, data.alt, data.platelets);
  const localInterpretation = interpretFib4(localScore, data.age);

  // Auto-orchestrate backend clinical assessment from verified observation
  useEffect(() => {
    let isSubscribed = true;

    async function orchestrateAssessment() {
      if (!data.patientId || !data.observationId || !data.verifiedByDoctor) {
        return;
      }
      if (hasTriggeredRef.current && assessment) {
        return;
      }

      setIsPersisting(true);
      setPersistError(null);

      try {
        const res = await createAssessment({
          patient_id: data.patientId,
          observation_id: data.observationId,
          clinician_notes: data.clinicianNotes,
        });

        if (isSubscribed) {
          hasTriggeredRef.current = true;
          setAssessment(res);
          onAssessmentCreated?.(res.id);
        }
      } catch (err: any) {
        if (isSubscribed) {
          setPersistError(err?.message || 'Failed to persist assessment in database.');
        }
      } finally {
        if (isSubscribed) {
          setIsPersisting(false);
        }
      }
    }

    orchestrateAssessment();

    return () => {
      isSubscribed = false;
    };
  }, [data.patientId, data.observationId, data.verifiedByDoctor, data.clinicianNotes]);

  const activeScore = assessment ? assessment.fib4_score : localScore;
  const activeCategory = assessment ? assessment.fib4_risk_category : localInterpretation.category;
  const interpretation = interpretFib4(activeScore, data.age);

  // Math breakdown
  const numerator = (data.age * data.ast).toFixed(1);
  const sqrtAlt = Math.sqrt(data.alt).toFixed(2);
  const denominator = (data.platelets * Math.sqrt(data.alt)).toFixed(1);

  const lowCutoff = data.age >= 65 ? 2.0 : 1.3;

  return (
    <div className="space-y-6">
      {/* Step Header */}
      <div className="border-b border-[#153568] pb-4">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <div>
            <span className="badge badge-ice mb-2">Step 3 of 5</span>
            <h1 className="h1 flex items-center gap-2">
              <Calculator className="text-ice" size={26} />
              Conventional Baseline: FIB-4 Score Calculation
            </h1>
          </div>
          <span className="badge badge-navy">Evidence-Based Risk Stratification</span>
        </div>
        <p className="text-muted mt-2" style={{ fontSize: '0.92rem' }}>
          FIB-4 is the guideline-recommended primary non-invasive triaging score (AASLD/EASL) used to rule out advanced liver fibrosis in primary care and hepatology clinics.
        </p>
      </div>

      {/* Main Score Display & Dial Card */}
      <div className="grid grid-12 gap-6">
        <div className="col-span-6 sugar-card space-y-5">
          <div className="card-header flex items-center justify-between">
            <h2 className="h2" style={{ fontSize: '1.15rem' }}>
              Calculated FIB-4 Index
            </h2>
            <span
              className={`badge ${
                interpretation.category === 'Low Risk'
                  ? 'badge-success'
                  : interpretation.category === 'Indeterminate'
                  ? 'badge-warning'
                  : 'badge-danger'
              }`}
            >
              {interpretation.category}
            </span>
          </div>

          {/* Large Hero Score */}
          <div
            style={{
              textAlign: 'center',
              padding: '24px 16px',
              background: 'rgba(10, 14, 28, 0.85)',
              border: '1px solid var(--navy-clinical)',
              borderRadius: '12px',
            }}
          >
            <div style={{ fontSize: '0.85rem', color: '#80B3D0', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Stratification Score
            </div>
            <div
              style={{
                fontFamily: 'JetBrains Mono',
                fontSize: '3.6rem',
                fontWeight: 700,
                color:
                  interpretation.category === 'Low Risk'
                    ? '#34D399'
                    : interpretation.category === 'Indeterminate'
                    ? '#FBBF24'
                    : '#F87171',
                lineHeight: 1.1,
                margin: '8px 0',
              }}
            >
              {activeScore.toFixed(2)}
            </div>
            <div style={{ fontSize: '0.86rem', color: '#cbd5e1' }}>
              Risk Category: <strong>{activeCategory}</strong>
              {assessment?.fib4_cutoff_applied ? (
                <span style={{ color: '#A9D4E7', display: 'block', marginTop: '2px', fontSize: '0.8rem' }}>
                  Cutoff Applied: {assessment.fib4_cutoff_applied}
                </span>
              ) : data.age >= 65 ? (
                ' (Age-Adjusted Cutoff Applied)'
              ) : null}
            </div>

            {isPersisting && (
              <div style={{ marginTop: '10px' }}>
                <span className="badge badge-ice" style={{ fontSize: '0.74rem' }}>
                  <Loader2 size={12} className="animate-spin inline mr-1" /> Persisting Assessment to Database...
                </span>
              </div>
            )}

            {assessment && (
              <div style={{ marginTop: '10px' }}>
                <span className="badge badge-success" style={{ fontSize: '0.74rem' }}>
                  <Database size={12} className="inline mr-1" /> Assessment ID: #{assessment.id.slice(0, 8)} (Encounter Recorded)
                </span>
              </div>
            )}

            {persistError && (
              <div style={{ marginTop: '10px', fontSize: '0.78rem', color: '#f87171' }}>
                Notice: {persistError} (Operating in client-calculation mode)
              </div>
            )}
          </div>

          {/* Three-Zone Cutoff Visualizer */}
          <div className="space-y-2">
            <div className="flex justify-between text-xs text-muted font-mono">
              <span>0.0</span>
              <span>Low Cutoff: {lowCutoff.toFixed(2)}</span>
              <span>High Cutoff: 2.67</span>
              <span>6.0+</span>
            </div>

            {/* Gradient Bar with Marker */}
            <div
              style={{
                position: 'relative',
                height: '14px',
                borderRadius: '7px',
                background: 'linear-gradient(90deg, #10B981 0%, #10B981 25%, #F59E0B 26%, #F59E0B 55%, #EF4444 56%, #EF4444 100%)',
                overflow: 'visible',
              }}
            >
              {/* Score Indicator Pointer */}
              <div
                style={{
                  position: 'absolute',
                  top: '-4px',
                  bottom: '-4px',
                  left: `${Math.min(98, Math.max(2, (activeScore / 4.5) * 100))}%`,
                  width: '6px',
                  borderRadius: '3px',
                  background: '#ffffff',
                  boxShadow: '0 0 10px #ffffff, 0 0 4px #000000',
                  transform: 'translateX(-50%)',
                  zIndex: 2,
                }}
              />
            </div>

            <div className="flex justify-between text-xs text-muted" style={{ fontSize: '0.74rem' }}>
              <span className="text-emerald-400">Low Risk (F0–F2 likely)</span>
              <span className="text-amber-300">Indeterminate Zone</span>
              <span className="text-rose-400">High Risk (F3–F4 likely)</span>
            </div>
          </div>

          {/* Interpretation Details Box */}
          <div
            style={{
              padding: '14px 18px',
              borderRadius: '10px',
              border: '1px solid',
            }}
            className={interpretation.colorClass}
          >
            <h4 style={{ color: '#ffffff', fontSize: '0.92rem', margin: '0 0 4px', textTransform: 'none' }}>
              Clinical Interpretation:
            </h4>
            <p style={{ fontSize: '0.86rem', margin: 0, lineHeight: 1.45 }}>
              {interpretation.description}
            </p>
            <div style={{ marginTop: '8px', paddingTop: '8px', borderTop: '1px solid rgba(255,255,255,0.1)' }}>
              <strong style={{ fontSize: '0.8rem', color: '#ffffff' }}>Actionable Guidance:</strong>
              <p style={{ fontSize: '0.82rem', margin: '2px 0 0' }}>
                {interpretation.recommendation}
              </p>
            </div>
          </div>
        </div>

        {/* Right Column: Mathematical Breakdown & Scientific Caveats */}
        <div className="col-span-6 space-y-4">
          {/* Formula Breakdown */}
          <div className="sugar-card space-y-4">
            <h3 style={{ fontSize: '1.05rem', color: '#ffffff', margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Info size={18} style={{ color: '#A9D4E7' }} />
              <span>Standard Formula & Component Values</span>
            </h3>

            <div
              style={{
                background: 'rgba(16, 16, 82, 0.4)',
                border: '1px solid var(--navy-clinical)',
                borderRadius: '8px',
                padding: '14px',
                fontFamily: 'JetBrains Mono',
                fontSize: '0.88rem',
                textAlign: 'center',
              }}
            >
              <div style={{ color: '#A9D4E7', marginBottom: '6px' }}>
                FIB-4 = (Age [years] × AST [U/L]) / (Platelets [10⁹/L] × √ALT [U/L])
              </div>
              <div style={{ color: '#ffffff', fontSize: '0.92rem' }}>
                = ({data.age} × {data.ast}) / ({data.platelets} × √{data.alt})
              </div>
              <div style={{ color: '#80B3D0', fontSize: '0.82rem', marginTop: '4px' }}>
                = {numerator} / ({data.platelets} × {sqrtAlt}) = {numerator} / {denominator} = <strong>{activeScore.toFixed(2)}</strong>
              </div>
            </div>

            {/* Input Variables Verification Table */}
            <table className="sugar-table" style={{ fontSize: '0.82rem' }}>
              <thead>
                <tr>
                  <th>Input Variable</th>
                  <th>Value</th>
                  <th>Reference</th>
                  <th>Formula Role</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>Age</td>
                  <td className="font-mono text-white">{data.age} yrs</td>
                  <td>18–100</td>
                  <td className="text-muted">Numerator (direct multiplier)</td>
                </tr>
                <tr>
                  <td>AST (SGOT)</td>
                  <td className="font-mono text-white">{data.ast} U/L</td>
                  <td>10–40</td>
                  <td className="text-muted">Numerator (hepatocyte injury)</td>
                </tr>
                <tr>
                  <td>Platelets</td>
                  <td className="font-mono text-white">{data.platelets} ×10³/μL</td>
                  <td>150–450</td>
                  <td className="text-muted">Denominator (portal hypertension/hypersplenism)</td>
                </tr>
                <tr>
                  <td>ALT (SGPT)</td>
                  <td className="font-mono text-white">{data.alt} U/L</td>
                  <td>7–56</td>
                  <td className="text-muted">Denominator (square root normalization)</td>
                </tr>
              </tbody>
            </table>
          </div>

          {/* Scientific Caveats & Known Pitfalls */}
          <div
            style={{
              background: 'rgba(21, 53, 104, 0.35)',
              border: '1px solid var(--navy-clinical)',
              borderRadius: '10px',
              padding: '16px',
            }}
            className="space-y-2"
          >
            <div className="flex items-center gap-2 text-amber-300 font-medium text-xs">
              <AlertTriangle size={15} />
              <span>Critical Scientific & Clinical Limitations</span>
            </div>
            <ul style={{ fontSize: '0.8rem', color: '#cbd5e1', paddingLeft: '18px', margin: 0, lineHeight: 1.5 }}>
              <li>
                <strong>FIB-4 is not a liver biopsy:</strong> It is a surrogate risk marker, not a histological F0–F4 grade diagnosis.
              </li>
              <li>
                <strong>Age dependency:</strong> In patients under 35, FIB-4 has lower sensitivity; in patients over 65, lower cutoffs yield false positives (adjusted to 2.00).
              </li>
              <li>
                <strong>Acute hepatitis flares:</strong> Acute alcohol, viral, or drug-induced transaminitis falsely elevates FIB-4 without true chronic architectural fibrosis.
              </li>
              <li>
                <strong>Indeterminate zone:</strong> 30–50% of routine patients fall in the 1.30–2.67 indeterminate category, requiring sequential elastography (VCTE).
              </li>
            </ul>
          </div>
        </div>
      </div>

      {/* Navigation Controls */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          paddingTop: '16px',
          borderTop: '1px solid var(--navy-clinical)',
        }}
      >
        <button
          type="button"
          onClick={onBack}
          className="btn btn-secondary flex items-center gap-2"
        >
          <ArrowLeft size={16} />
          <span>Back to Value Verification</span>
        </button>

        <button
          type="button"
          onClick={onProceed}
          className="btn btn-primary flex items-center gap-2"
          style={{ padding: '12px 28px', fontSize: '0.95rem' }}
        >
          <span>Compare Progressive Machine Learning Pipeline (Step 4)</span>
          <ArrowRight size={18} />
        </button>
      </div>
    </div>
  );
};
