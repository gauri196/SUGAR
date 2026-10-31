// SUGAR — Step 5: Unified Clinical Assessment Results Experience
import React, { useState, useEffect } from 'react';
import {
  ClipboardCheck,
  Printer,
  RotateCcw,
  ShieldAlert,
  ArrowLeft,
  Info,
  GitBranch,
  Sliders,
  ExternalLink,
  History,
  Loader2,
} from 'lucide-react';
import { ClinicalInputs, PredictionResponse, AssessmentListResponse } from '../../types';
import { calculateFib4, interpretFib4, getPatientAssessments } from '../../services/api';

interface AssessmentResultsProps {
  data: ClinicalInputs;
  predictionResult: PredictionResponse | null;
  onReset: () => void;
  onBack: () => void;
  onNavigateToResearch: () => void;
}

export const AssessmentResults: React.FC<AssessmentResultsProps> = ({
  data,
  predictionResult,
  onReset,
  onBack,
  onNavigateToResearch,
}) => {
  const [history, setHistory] = useState<AssessmentListResponse | null>(null);
  const [loadingHistory, setLoadingHistory] = useState<boolean>(false);
  const [historyError, setHistoryError] = useState<string | null>(null);

  useEffect(() => {
    let isSubscribed = true;
    async function fetchHistory() {
      if (!data.patientId) return;
      setLoadingHistory(true);
      try {
        const res = await getPatientAssessments(data.patientId, 0, 10);
        if (isSubscribed) {
          setHistory(res);
        }
      } catch (err: any) {
        if (isSubscribed) {
          setHistoryError(err?.message || 'Could not load patient assessment history.');
        }
      } finally {
        if (isSubscribed) {
          setLoadingHistory(false);
        }
      }
    }
    fetchHistory();
    return () => {
      isSubscribed = false;
    };
  }, [data.patientId]);

  const fib4Score = calculateFib4(data.age, data.ast, data.alt, data.platelets);
  const interpretation = interpretFib4(fib4Score, data.age);

  // Concordance check between FIB-4 and ML models
  const fib4Risk = interpretation.category; // 'Low Risk' | 'Indeterminate' | 'High Risk'
  const modelARisk = predictionResult
    ? predictionResult.baseline_model.prediction === 1
      ? 'Elevated'
      : 'Low'
    : 'Pending';
  const modelBRisk = predictionResult
    ? predictionResult.expanded_model.prediction === 1
      ? 'Elevated'
      : 'Low'
    : 'Pending';

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="space-y-6">
      {/* Step Header with Actions */}
      <div className="border-b border-[#153568] pb-4 flex items-center justify-between flex-wrap gap-4">
        <div>
          <span className="badge badge-success mb-2">Step 5 of 5 • Completed</span>
          <h1 className="h1 flex items-center gap-2">
            <ClipboardCheck className="text-ice" size={26} />
            Patient Liver Fibrosis Assessment Report
          </h1>
          <p className="text-muted mt-1" style={{ fontSize: '0.92rem' }}>
            Comprehensive clinical risk stratification synthesizing verified laboratory biomarkers, baseline FIB-4, and machine learning models.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={handlePrint}
            className="btn btn-secondary flex items-center gap-2"
          >
            <Printer size={16} />
            <span>Print / Save PDF</span>
          </button>

          <button
            type="button"
            onClick={onReset}
            className="btn btn-primary flex items-center gap-2"
          >
            <RotateCcw size={16} />
            <span>New Assessment</span>
          </button>
        </div>
      </div>

      {/* Summary Banner */}
      <div
        style={{
          background: 'rgba(10, 14, 28, 0.9)',
          border: '1px solid var(--navy-clinical)',
          borderRadius: '12px',
          padding: '20px 24px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '16px',
        }}
      >
        <div>
          <div style={{ fontSize: '0.8rem', color: '#80B3D0', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Executive Clinical Finding
          </div>
          <div style={{ fontSize: '1.35rem', fontWeight: 700, color: '#ffffff', marginTop: '2px' }}>
            FIB-4 Stratification: <span className={fib4Risk === 'Low Risk' ? 'text-emerald-400' : fib4Risk === 'Indeterminate' ? 'text-amber-300' : 'text-rose-400'}>{fib4Risk}</span> (Score: {fib4Score.toFixed(2)})
          </div>
          <div style={{ fontSize: '0.86rem', color: '#cbd5e1', marginTop: '4px' }}>
            {interpretation.recommendation}
          </div>
        </div>

        <div style={{ display: 'flex', gap: '12px', alignItems: 'center', flexWrap: 'wrap' }}>
          <div
            style={{
              textAlign: 'center',
              padding: '8px 14px',
              background: 'rgba(21, 53, 104, 0.4)',
              border: '1px solid var(--border-subtle)',
              borderRadius: '8px',
            }}
          >
            <span style={{ fontSize: '0.72rem', color: '#80B3D0', display: 'block' }}>Verified By</span>
            <span style={{ fontSize: '0.86rem', color: '#ffffff', fontWeight: 600 }}>
              {data.verifiedBy || 'Doctor Confirmed'}
            </span>
          </div>

          <div
            style={{
              textAlign: 'center',
              padding: '8px 14px',
              background: 'rgba(21, 53, 104, 0.4)',
              border: '1px solid var(--border-subtle)',
              borderRadius: '8px',
            }}
          >
            <span style={{ fontSize: '0.72rem', color: '#80B3D0', display: 'block' }}>Source</span>
            <span style={{ fontSize: '0.86rem', color: '#A9D4E7', fontWeight: 600, fontFamily: 'JetBrains Mono' }}>
              {data.reportSource ? data.reportSource.toUpperCase() : 'MANUAL'}
            </span>
          </div>

          {data.patientId && (
            <div
              style={{
                textAlign: 'center',
                padding: '8px 14px',
                background: 'rgba(21, 53, 104, 0.4)',
                border: '1px solid var(--border-subtle)',
                borderRadius: '8px',
              }}
            >
              <span style={{ fontSize: '0.72rem', color: '#80B3D0', display: 'block' }}>Patient Token</span>
              <span style={{ fontSize: '0.82rem', color: '#A9D4E7', fontWeight: 600, fontFamily: 'JetBrains Mono' }}>
                {data.patientId.slice(0, 8)}...
              </span>
            </div>
          )}

          {data.assessmentId && (
            <div
              style={{
                textAlign: 'center',
                padding: '8px 14px',
                background: 'rgba(16, 185, 129, 0.15)',
                border: '1px solid rgba(52, 211, 153, 0.4)',
                borderRadius: '8px',
              }}
            >
              <span style={{ fontSize: '0.72rem', color: '#34D399', display: 'block' }}>Assessment DB</span>
              <span style={{ fontSize: '0.82rem', color: '#ffffff', fontWeight: 600, fontFamily: 'JetBrains Mono' }}>
                #{data.assessmentId.slice(0, 8)}
              </span>
            </div>
          )}
        </div>
      </div>

      <div className="grid grid-12 gap-6">
        {/* Left Column: Verified Biomarker Inputs Table */}
        <div className="col-span-5 space-y-4">
          <div className="sugar-card space-y-4">
            <div className="card-header flex items-center justify-between">
              <h3 style={{ fontSize: '1.05rem', color: '#ffffff', margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Sliders size={18} style={{ color: '#A9D4E7' }} />
                <span>Verified Patient Biomarkers</span>
              </h3>
              <span className="badge badge-success">Reviewed</span>
            </div>

            <table className="sugar-table" style={{ fontSize: '0.82rem' }}>
              <thead>
                <tr>
                  <th>Biomarker</th>
                  <th>Value</th>
                  <th>Reference</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>Age</td>
                  <td className="font-mono text-white font-medium">{data.age} yrs</td>
                  <td>18–100</td>
                  <td><span className="badge badge-ice">Normal</span></td>
                </tr>
                <tr>
                  <td>Platelets</td>
                  <td className="font-mono text-white font-medium">{data.platelets} ×10³/μL</td>
                  <td>150–450</td>
                  <td>
                    {data.platelets < 150 ? (
                      <span className="badge badge-warning">Thrombocytopenia</span>
                    ) : (
                      <span className="badge badge-ice">Normal</span>
                    )}
                  </td>
                </tr>
                <tr>
                  <td>AST (SGOT)</td>
                  <td className="font-mono text-white font-medium">{data.ast} U/L</td>
                  <td>10–40</td>
                  <td>
                    {data.ast > 40 ? (
                      <span className="badge badge-danger">Elevated</span>
                    ) : (
                      <span className="badge badge-ice">Normal</span>
                    )}
                  </td>
                </tr>
                <tr>
                  <td>ALT (SGPT)</td>
                  <td className="font-mono text-white font-medium">{data.alt} U/L</td>
                  <td>7–56</td>
                  <td>
                    {data.alt > 56 ? (
                      <span className="badge badge-danger">Elevated</span>
                    ) : (
                      <span className="badge badge-ice">Normal</span>
                    )}
                  </td>
                </tr>
                <tr>
                  <td>Body Mass Index</td>
                  <td className="font-mono text-white font-medium">{data.bmi.toFixed(1)} kg/m²</td>
                  <td>18.5–24.9</td>
                  <td>
                    {data.bmi >= 30 ? (
                      <span className="badge badge-warning">Obese</span>
                    ) : data.bmi >= 25 ? (
                      <span className="badge badge-navy">Overweight</span>
                    ) : (
                      <span className="badge badge-ice">Normal</span>
                    )}
                  </td>
                </tr>
                <tr>
                  <td>WBC Count</td>
                  <td className="font-mono text-white font-medium">{data.wbc.toFixed(1)} ×10³/μL</td>
                  <td>4.5–11.0</td>
                  <td><span className="badge badge-ice">Normal</span></td>
                </tr>
                <tr>
                  <td>RBC Count</td>
                  <td className="font-mono text-white font-medium">{data.rbc.toFixed(2)} ×10⁶/μL</td>
                  <td>4.2–5.9</td>
                  <td><span className="badge badge-ice">Normal</span></td>
                </tr>
                <tr>
                  <td>Hemoglobin (HGB)</td>
                  <td className="font-mono text-white font-medium">{data.hgb.toFixed(1)} g/dL</td>
                  <td>12.0–17.5</td>
                  <td><span className="badge badge-ice">Normal</span></td>
                </tr>
                {data.glucose && (
                  <tr>
                    <td>Fasting Glucose</td>
                    <td className="font-mono text-white font-medium">{data.glucose} mg/dL</td>
                    <td>70–99</td>
                    <td><span className="badge badge-navy">Metabolic</span></td>
                  </tr>
                )}
                {data.capSteatosis && (
                  <tr>
                    <td>CAP Steatosis</td>
                    <td className="font-mono text-white font-medium">{data.capSteatosis} dB/m</td>
                    <td>&lt; 238</td>
                    <td><span className="badge badge-navy">Steatosis</span></td>
                  </tr>
                )}
              </tbody>
            </table>

            {data.etiology && (
              <div style={{ fontSize: '0.8rem', color: '#80B3D0', borderTop: '1px solid var(--navy-clinical)', paddingTop: '8px' }}>
                Presumed Etiology: <strong style={{ color: '#ffffff' }}>{data.etiology.toUpperCase()}</strong>
                {data.jaundice && ' • Scleral Jaundice Present'}
                {data.hepatomegaly && ' • Hepatomegaly'}
                {data.ascites && ' • Ascites'}
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Comparison Matrix & Concordance */}
        <div className="col-span-7 space-y-4">
          {/* Side-by-Side Model Comparison Table */}
          <div className="sugar-card space-y-4">
            <div className="card-header flex items-center justify-between">
              <h3 style={{ fontSize: '1.05rem', color: '#ffffff', margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
                <GitBranch size={18} style={{ color: '#A9D4E7' }} />
                <span>Side-by-Side Model Comparison Matrix</span>
              </h3>
              <span className="badge badge-navy">Research Pipeline</span>
            </div>

            <table className="sugar-table" style={{ fontSize: '0.82rem' }}>
              <thead>
                <tr>
                  <th>Model Tier</th>
                  <th>Features Included</th>
                  <th>Evaluation Engine</th>
                  <th>Output / Status</th>
                </tr>
              </thead>
              <tbody>
                {/* FIB-4 Baseline */}
                <tr className="highlight">
                  <td>
                    <strong style={{ color: '#A9D4E7' }}>Conventional FIB-4</strong>
                    <div style={{ fontSize: '0.74rem', color: '#80B3D0' }}>AASLD/EASL Baseline</div>
                  </td>
                  <td>Age, AST, Platelets, ALT</td>
                  <td className="font-mono">Direct Formula</td>
                  <td>
                    <span
                      className={`badge ${
                        interpretation.category === 'Low Risk'
                          ? 'badge-success'
                          : interpretation.category === 'Indeterminate'
                          ? 'badge-warning'
                          : 'badge-danger'
                      }`}
                    >
                      {interpretation.category} ({fib4Score.toFixed(2)})
                    </span>
                  </td>
                </tr>

                {/* Model A */}
                <tr>
                  <td>
                    <strong style={{ color: '#ffffff' }}>Model A</strong>
                    <div style={{ fontSize: '0.74rem', color: '#80B3D0' }}>Routine Baseline</div>
                  </td>
                  <td>Age, BMI, Plat, AST, ALT</td>
                  <td className="font-mono">Logistic Regression (FastAPI)</td>
                  <td>
                    {predictionResult ? (
                      <div>
                        <span
                          className={`badge ${
                            predictionResult.baseline_model.prediction === 1 ? 'badge-danger' : 'badge-success'
                          }`}
                        >
                          {predictionResult.baseline_model.prediction === 1 ? 'Elevated Risk' : 'Low Risk'}
                        </span>
                        <span className="font-mono text-muted text-xs ml-2">
                          {(predictionResult.baseline_model.probability * 100).toFixed(1)}%
                        </span>
                      </div>
                    ) : (
                      <span className="text-muted">Awaiting backend</span>
                    )}
                  </td>
                </tr>

                {/* Model B */}
                <tr>
                  <td>
                    <strong style={{ color: '#ffffff' }}>Model B</strong>
                    <div style={{ fontSize: '0.74rem', color: '#80B3D0' }}>Expanded Fibrosis</div>
                  </td>
                  <td>Model A + WBC, RBC, HGB</td>
                  <td className="font-mono">Random Forest (FastAPI)</td>
                  <td>
                    {predictionResult ? (
                      <div>
                        <span
                          className={`badge ${
                            predictionResult.expanded_model.prediction === 1 ? 'badge-danger' : 'badge-success'
                          }`}
                        >
                          {predictionResult.expanded_model.prediction === 1 ? 'Elevated Risk' : 'Low Risk'}
                        </span>
                        <span className="font-mono text-muted text-xs ml-2">
                          {(predictionResult.expanded_model.probability * 100).toFixed(1)}%
                        </span>
                      </div>
                    ) : (
                      <span className="text-muted">Awaiting backend</span>
                    )}
                  </td>
                </tr>

                {/* Model C */}
                <tr style={{ opacity: 0.85 }}>
                  <td>
                    <strong style={{ color: '#cbd5e1' }}>Model C</strong>
                    <div style={{ fontSize: '0.74rem', color: '#80B3D0' }}>Metabolic Expansion</div>
                  </td>
                  <td>Model B + Glucose, Chol, CAP</td>
                  <td className="font-mono">NHANES 8H / UCI HCV</td>
                  <td>
                    <span className="badge badge-navy">Research Completed (Offline)</span>
                  </td>
                </tr>

                {/* Model D */}
                <tr style={{ opacity: 0.95 }}>
                  <td>
                    <strong style={{ color: '#cbd5e1' }}>Model D</strong>
                    <div style={{ fontSize: '0.74rem', color: '#6EE7B7' }}>Etiology & Stigmata</div>
                  </td>
                  <td>Biomarkers + Ascites, Hepatomegaly, Spiders, Edema</td>
                  <td className="font-mono">Mayo Clinic PBC (N=418)</td>
                  <td>
                    <span className="badge badge-success" style={{ background: 'rgba(16, 185, 129, 0.2)', color: '#6EE7B7', border: '1px solid #10B981' }}>
                      Trained Pipeline (ROC-AUC 0.710)
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          {/* Diagnostic Concordance Analysis */}
          <div
            style={{
              background: 'rgba(10, 14, 28, 0.85)',
              border: '1px solid var(--navy-clinical)',
              borderRadius: '10px',
              padding: '16px',
            }}
            className="space-y-2"
          >
            <h4 style={{ color: '#ffffff', fontSize: '0.92rem', margin: 0, textTransform: 'none', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Info size={16} style={{ color: '#A9D4E7' }} />
              <span>Diagnostic Concordance & Explanation</span>
            </h4>
            <p style={{ fontSize: '0.84rem', color: '#cbd5e1', lineHeight: 1.5, margin: 0 }}>
              {fib4Risk === 'Low Risk' && modelBRisk === 'Low' && (
                <>
                  <strong>High Concordance:</strong> Both conventional FIB-4 ({fib4Score.toFixed(2)}) and the Expanded Random Forest model ({predictionResult ? (predictionResult.expanded_model.probability * 100).toFixed(1) : 0}%) classify this patient as low risk for advanced liver fibrosis. Standard primary care monitoring is advised.
                </>
              )}
              {fib4Risk === 'High Risk' && modelBRisk === 'Elevated' && (
                <>
                  <strong>High Concordance:</strong> Both FIB-4 ({fib4Score.toFixed(2)}) and Expanded ML ({predictionResult ? (predictionResult.expanded_model.probability * 100).toFixed(1) : 0}%) indicate elevated risk of advanced fibrosis (Metavir F3–F4). Hepatology referral and ultrasound screening are clinically indicated.
                </>
              )}
              {fib4Risk === 'Indeterminate' && (
                <>
                  <strong>Indeterminate Triage:</strong> Conventional FIB-4 is in the grey zone (1.30–2.67), where blood markers alone cannot rule in or out advanced fibrosis. Expanded Random Forest assigns a probability of {predictionResult ? (predictionResult.expanded_model.probability * 100).toFixed(1) : 0}%. As per clinical practice guidelines, secondary evaluation with VCTE FibroScan elastography is strongly recommended.
                </>
              )}
              {fib4Risk === 'Low Risk' && modelBRisk === 'Elevated' && (
                <>
                  <strong>Discordance Detected:</strong> FIB-4 indicates Low Risk ({fib4Score.toFixed(2)}), whereas Expanded Model B indicates elevated risk ({predictionResult ? (predictionResult.expanded_model.probability * 100).toFixed(1) : 0}%). This typically occurs when hematologic markers (such as elevated WBC or subclinical platelet decline) influence the non-linear Random Forest ensemble. Clinical correlation and secondary elastography are recommended.
                </>
              )}
              {fib4Risk === 'High Risk' && modelBRisk === 'Low' && (
                <>
                  <strong>Discordance Detected:</strong> FIB-4 is elevated ({fib4Score.toFixed(2)}), but Model B indicates lower probability ({predictionResult ? (predictionResult.expanded_model.probability * 100).toFixed(1) : 0}%). Transaminase elevations without corresponding hematologic shifts can inflate FIB-4. Consider secondary VCTE elastography.
                </>
              )}
            </p>
          </div>

          {/* Scientific Disclaimer & Regulatory Notice */}
          <div
            style={{
              background: 'rgba(21, 53, 104, 0.3)',
              border: '1px solid var(--navy-clinical)',
              borderRadius: '10px',
              padding: '14px 16px',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#FBBF24', fontSize: '0.84rem', fontWeight: 600, marginBottom: '4px' }}>
              <ShieldAlert size={16} />
              <span>Regulatory & Research Protocol Advisory</span>
            </div>
            <p style={{ fontSize: '0.78rem', color: '#80B3D0', margin: 0, lineHeight: 1.45 }}>
              SUGAR is an investigational research prototype for non-invasive risk stratification. Models A and B are trained on retrospective research cohorts (UCI Egyptian HCV dataset, N=1,385) where AST 1 and ALT 1 represent dataset ratio features. This tool does not replace histological biopsy or licensed physician judgment.
            </p>
          </div>
        </div>
      </div>

      {/* Patient Longitudinal Assessment History */}
      {data.patientId && (
        <div className="sugar-card space-y-4">
          <div className="card-header flex items-center justify-between">
            <div className="flex items-center gap-2">
              <History size={18} style={{ color: '#A9D4E7' }} />
              <h3 style={{ fontSize: '1.05rem', color: '#ffffff', margin: 0 }}>
                Patient Longitudinal Assessment Encounters
              </h3>
            </div>
            <span className="badge badge-navy">
              {history ? `${history.total} Recorded Encounter${history.total === 1 ? '' : 's'}` : 'Loading History...'}
            </span>
          </div>

          {loadingHistory && (
            <div className="flex items-center gap-2 text-xs text-muted py-2">
              <Loader2 size={15} className="animate-spin text-ice" />
              <span>Fetching previous clinical assessments from database...</span>
            </div>
          )}

          {history && history.items.length > 0 && (
            <table className="sugar-table" style={{ fontSize: '0.82rem' }}>
              <thead>
                <tr>
                  <th>Encounter Date</th>
                  <th>Assessment ID</th>
                  <th>FIB-4 Score</th>
                  <th>Stratified Risk</th>
                  <th>Applied Cutoff</th>
                  <th>Clinician Notes</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {history.items.map((item) => (
                  <tr key={item.id} className={item.id === data.assessmentId ? 'highlight' : ''}>
                    <td className="font-mono text-muted">
                      {new Date(item.created_at).toLocaleDateString()}{' '}
                      {new Date(item.created_at).toLocaleTimeString([], {
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </td>
                    <td className="font-mono text-white">#{item.id.slice(0, 8)}</td>
                    <td className="font-mono text-white font-medium">{item.fib4_score.toFixed(2)}</td>
                    <td>
                      <span
                        className={`badge ${
                          item.fib4_risk_category === 'Low Risk'
                            ? 'badge-success'
                            : item.fib4_risk_category === 'Indeterminate'
                            ? 'badge-warning'
                            : 'badge-danger'
                        }`}
                        style={{ fontSize: '0.72rem' }}
                      >
                        {item.fib4_risk_category}
                      </span>
                    </td>
                    <td className="text-muted" style={{ fontSize: '0.76rem' }}>
                      {item.fib4_cutoff_applied}
                    </td>
                    <td className="text-secondary" style={{ fontSize: '0.76rem' }}>
                      {item.clinician_notes || '—'}
                    </td>
                    <td>
                      <span className="badge badge-ice" style={{ fontSize: '0.7rem' }}>
                        {item.status.toUpperCase()}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          {history && history.items.length === 0 && !loadingHistory && (
            <p style={{ fontSize: '0.82rem', color: '#80B3D0', margin: 0 }}>
              This is the initial baseline assessment recorded for this patient identifier.
            </p>
          )}

          {historyError && (
            <p style={{ fontSize: '0.8rem', color: '#f87171', margin: 0 }}>
              Note: {historyError}
            </p>
          )}
        </div>
      )}

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
          <span>Back to Model Pipeline Comparison</span>
        </button>

        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={onNavigateToResearch}
            className="btn btn-secondary flex items-center gap-2"
          >
            <ExternalLink size={16} />
            <span>Explore Research Lab Benchmarks</span>
          </button>

          <button
            type="button"
            onClick={onReset}
            className="btn btn-primary flex items-center gap-2"
          >
            <RotateCcw size={16} />
            <span>Start Another Assessment</span>
          </button>
        </div>
      </div>
    </div>
  );
};
