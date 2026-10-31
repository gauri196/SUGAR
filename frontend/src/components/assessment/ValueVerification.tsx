// SUGAR — Step 2: Extract & Verify Clinical Variables
import React, { useState } from 'react';
import {
  Sliders,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  ArrowLeft,
  ShieldCheck,
  HelpCircle,
  Activity,
  HeartPulse,
  Flame,
  Loader2,
} from 'lucide-react';
import { ClinicalInputs } from '../../types';
import {
  verifyObservation,
  registerReport,
  clinicalInputsToObservationPayload,
} from '../../services/api';

interface ValueVerificationProps {
  data: ClinicalInputs;
  onChange: (updated: ClinicalInputs) => void;
  onProceed: () => void;
  onBack: () => void;
}

export const ValueVerification: React.FC<ValueVerificationProps> = ({
  data,
  onChange,
  onProceed,
  onBack,
}) => {
  const [confirmed, setConfirmed] = useState<boolean>(data.verifiedByDoctor || false);
  const [clinicianId, setClinicianId] = useState<string>(data.verifiedBy || 'Dr. Staff Clinician');
  const [clinicianNotes, setClinicianNotes] = useState<string>(data.clinicianNotes || '');
  const [isVerifying, setIsVerifying] = useState<boolean>(false);
  const [verificationError, setVerificationError] = useState<string | null>(null);
  const [showValidationErrors, setShowValidationErrors] = useState<boolean>(false);

  // Field validation logic
  const isAgeValid = data.age >= 18 && data.age <= 100;
  const isPlateletsValid = data.platelets > 0 && data.platelets <= 1000;
  const isAstValid = data.ast > 0 && data.ast <= 2000;
  const isAltValid = data.alt > 0 && data.alt <= 2000;
  const isBmiValid = data.bmi >= 12 && data.bmi <= 70;
  const isWbcValid = data.wbc > 0 && data.wbc <= 100;
  const isRbcValid = data.rbc > 0 && data.rbc <= 10;
  const isHgbValid = data.hgb > 0 && data.hgb <= 25;

  const coreInputsValid = isAgeValid && isPlateletsValid && isAstValid && isAltValid;

  const handleFieldChange = (field: keyof ClinicalInputs, val: any) => {
    onChange({
      ...data,
      [field]: val,
      verifiedByDoctor: false, // Reset doctor confirmation when values change
    });
    setConfirmed(false);
  };

  const handleConfirmToggle = (checked: boolean) => {
    setConfirmed(checked);
    onChange({
      ...data,
      verifiedByDoctor: checked,
      verifiedBy: checked ? clinicianId : undefined,
      clinicianNotes,
    });
  };

  const handleNext = async () => {
    if (!coreInputsValid) {
      setShowValidationErrors(true);
      return;
    }
    if (!confirmed) {
      alert('Please check the confirmation box verifying that you have reviewed clinical values before proceeding.');
      return;
    }

    setIsVerifying(true);
    setVerificationError(null);

    try {
      let obsId = data.observationId;
      let patId = data.patientId;

      // Ensure observation exists in backend
      if (!obsId) {
        const regRes = await registerReport({
          original_filename: data.reportFilename || 'manual_entry.json',
          media_type: 'application/json',
          extraction_status: 'parsed',
          clinical_values: clinicalInputsToObservationPayload(data),
          uploaded_by: clinicianId,
        });
        obsId = regRes.observation_id;
        patId = regRes.patient_id;
      }

      // Call Phase 5 backend observation verification endpoint
      const verRes = await verifyObservation(obsId, {
        verified_by: clinicianId.trim() || 'Dr. Staff Clinician',
        verified_values: clinicalInputsToObservationPayload(data),
        clinician_notes: clinicianNotes.trim() || undefined,
      });

      onChange({
        ...data,
        patientId: patId || verRes.patient_id,
        observationId: verRes.observation_id,
        verifiedByDoctor: true,
        verifiedBy: verRes.verified_by,
        verifiedAt: verRes.verified_at,
        clinicianNotes,
      });

      onProceed();
    } catch (err: any) {
      setVerificationError(err?.message || 'Verification failed on backend.');
    } finally {
      setIsVerifying(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Step Header */}
      <div className="border-b border-[#153568] pb-4">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <div>
            <span className="badge badge-ice mb-2">Step 2 of 5</span>
            <h1 className="h1 flex items-center gap-2">
              <Sliders className="text-ice" size={26} />
              Verify & Edit Clinical Variables
            </h1>
          </div>
          <div className="flex items-center gap-2">
            <span
              className={`badge ${
                coreInputsValid ? 'badge-success' : 'badge-danger'
              }`}
            >
              {coreInputsValid ? 'FIB-4 Variables Valid' : 'Required Variables Incomplete'}
            </span>
          </div>
        </div>
        <p className="text-muted mt-2" style={{ fontSize: '0.92rem' }}>
          Review extracted laboratory values. Missing inputs are not silently imputed; unobserved parameters remain tracked explicitly. Clinician confirmation is required before model execution.
        </p>
      </div>

      {/* Validation Banner if errors exist */}
      {showValidationErrors && !coreInputsValid && (
        <div
          style={{
            background: 'rgba(239, 68, 68, 0.12)',
            border: '1px solid rgba(248, 113, 113, 0.4)',
            borderRadius: '10px',
            padding: '14px 18px',
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
          }}
        >
          <AlertTriangle size={20} className="text-rose-400" style={{ flexShrink: 0 }} />
          <div>
            <h4 style={{ color: '#ffffff', fontSize: '0.92rem', margin: 0, textTransform: 'none' }}>
              Required Core Variables Require Attention
            </h4>
            <p style={{ color: '#cbd5e1', fontSize: '0.84rem', margin: '2px 0 0' }}>
              FIB-4 and Model A require valid, non-zero values for Age, Platelet count, AST, and ALT to prevent mathematical division by zero.
            </p>
          </div>
        </div>
      )}

      {/* Grid of 4 Clinical Feature Groups */}
      <div className="grid grid-2 gap-6">
        {/* Panel 1: Core Routine Liver Variables (FIB-4 & Model A) */}
        <div className="sugar-card space-y-4">
          <div className="card-header flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Activity size={18} style={{ color: '#A9D4E7' }} />
              <h2 className="h2" style={{ fontSize: '1.1rem' }}>
                1. Core Routine Variables (FIB-4 & Baseline)
              </h2>
            </div>
            <span className="badge badge-ice">Required</span>
          </div>

          <div className="space-y-3">
            {/* Age */}
            <div>
              <div className="flex items-center justify-between text-xs mb-1">
                <label className="text-white font-medium">Age (years)</label>
                <span className="font-mono text-muted">Range: 18–100 yrs</span>
              </div>
              <div style={{ position: 'relative' }}>
                <input
                  type="number"
                  min="18"
                  max="100"
                  step="1"
                  value={data.age || ''}
                  onChange={(e) => handleFieldChange('age', parseFloat(e.target.value) || 0)}
                  className="sugar-input"
                  style={{
                    borderColor: !isAgeValid && showValidationErrors ? '#EF4444' : undefined,
                    paddingRight: '36px',
                  }}
                />
                <span style={{ position: 'absolute', right: '12px', top: '10px' }}>
                  {isAgeValid ? (
                    <CheckCircle2 size={16} className="text-emerald-400" />
                  ) : (
                    <AlertTriangle size={16} className="text-rose-400" />
                  )}
                </span>
              </div>
              {data.age >= 65 && (
                <span style={{ fontSize: '0.75rem', color: '#FBBF24', display: 'block', marginTop: '2px' }}>
                  Note: Age ≥ 65 adjusts low-risk FIB-4 cutoff from 1.30 to 2.00.
                </span>
              )}
            </div>

            {/* Platelets */}
            <div>
              <div className="flex items-center justify-between text-xs mb-1">
                <label className="text-white font-medium">Platelet Count (10³/μL or 10⁹/L)</label>
                <span className="font-mono text-muted">Normal: 150–450</span>
              </div>
              <div style={{ position: 'relative' }}>
                <input
                  type="number"
                  min="1"
                  max="1000"
                  step="1"
                  value={data.platelets || ''}
                  onChange={(e) => handleFieldChange('platelets', parseFloat(e.target.value) || 0)}
                  className="sugar-input"
                  style={{
                    borderColor: !isPlateletsValid && showValidationErrors ? '#EF4444' : undefined,
                    paddingRight: '36px',
                  }}
                />
                <span style={{ position: 'absolute', right: '12px', top: '10px' }}>
                  {isPlateletsValid ? (
                    <CheckCircle2 size={16} className="text-emerald-400" />
                  ) : (
                    <AlertTriangle size={16} className="text-rose-400" />
                  )}
                </span>
              </div>
            </div>

            {/* AST 1 */}
            <div>
              <div className="flex items-center justify-between text-xs mb-1">
                <label className="text-white font-medium">AST (Aspartate Aminotransferase) [AST 1]</label>
                <span className="font-mono text-muted">Normal: 10–40 U/L</span>
              </div>
              <div style={{ position: 'relative' }}>
                <input
                  type="number"
                  min="1"
                  max="2000"
                  step="1"
                  value={data.ast || ''}
                  onChange={(e) => handleFieldChange('ast', parseFloat(e.target.value) || 0)}
                  className="sugar-input"
                  style={{
                    borderColor: !isAstValid && showValidationErrors ? '#EF4444' : undefined,
                    paddingRight: '36px',
                  }}
                />
                <span style={{ position: 'absolute', right: '12px', top: '10px' }}>
                  {isAstValid ? (
                    <CheckCircle2 size={16} className="text-emerald-400" />
                  ) : (
                    <AlertTriangle size={16} className="text-rose-400" />
                  )}
                </span>
              </div>
            </div>

            {/* ALT 1 */}
            <div>
              <div className="flex items-center justify-between text-xs mb-1">
                <label className="text-white font-medium">ALT (Alanine Aminotransferase) [ALT 1]</label>
                <span className="font-mono text-muted">Normal: 7–56 U/L</span>
              </div>
              <div style={{ position: 'relative' }}>
                <input
                  type="number"
                  min="1"
                  max="2000"
                  step="1"
                  value={data.alt || ''}
                  onChange={(e) => handleFieldChange('alt', parseFloat(e.target.value) || 0)}
                  className="sugar-input"
                  style={{
                    borderColor: !isAltValid && showValidationErrors ? '#EF4444' : undefined,
                    paddingRight: '36px',
                  }}
                />
                <span style={{ position: 'absolute', right: '12px', top: '10px' }}>
                  {isAltValid ? (
                    <CheckCircle2 size={16} className="text-emerald-400" />
                  ) : (
                    <AlertTriangle size={16} className="text-rose-400" />
                  )}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Panel 2: Expanded Hematologic Variables (Model B) */}
        <div className="sugar-card space-y-4">
          <div className="card-header flex items-center justify-between">
            <div className="flex items-center gap-2">
              <HeartPulse size={18} style={{ color: '#A9D4E7' }} />
              <h2 className="h2" style={{ fontSize: '1.1rem' }}>
                2. Expanded Clinical & CBC Markers (Model B)
              </h2>
            </div>
            <span className="badge badge-navy">Model B Input</span>
          </div>

          <div className="space-y-3">
            {/* BMI */}
            <div>
              <div className="flex items-center justify-between text-xs mb-1">
                <label className="text-white font-medium">Body Mass Index (BMI, kg/m²)</label>
                <span className="font-mono text-muted">Normal: 18.5–24.9</span>
              </div>
              <input
                type="number"
                min="12"
                max="70"
                step="0.1"
                value={data.bmi || ''}
                onChange={(e) => handleFieldChange('bmi', parseFloat(e.target.value) || 0)}
                className="sugar-input"
              />
            </div>

            {/* WBC */}
            <div>
              <div className="flex items-center justify-between text-xs mb-1">
                <label className="text-white font-medium">White Blood Cell Count (WBC, 10³/μL)</label>
                <span className="font-mono text-muted">Normal: 4.5–11.0</span>
              </div>
              <input
                type="number"
                min="0.5"
                max="100"
                step="0.1"
                value={data.wbc || ''}
                onChange={(e) => handleFieldChange('wbc', parseFloat(e.target.value) || 0)}
                className="sugar-input"
              />
            </div>

            {/* RBC */}
            <div>
              <div className="flex items-center justify-between text-xs mb-1">
                <label className="text-white font-medium">Red Blood Cell Count (RBC, 10⁶/μL)</label>
                <span className="font-mono text-muted">Normal: 4.2–5.9</span>
              </div>
              <input
                type="number"
                min="1.0"
                max="10"
                step="0.05"
                value={data.rbc || ''}
                onChange={(e) => handleFieldChange('rbc', parseFloat(e.target.value) || 0)}
                className="sugar-input"
              />
            </div>

            {/* HGB */}
            <div>
              <div className="flex items-center justify-between text-xs mb-1">
                <label className="text-white font-medium">Hemoglobin (HGB, g/dL)</label>
                <span className="font-mono text-muted">Normal: 12.0–17.5</span>
              </div>
              <input
                type="number"
                min="3"
                max="25"
                step="0.1"
                value={data.hgb || ''}
                onChange={(e) => handleFieldChange('hgb', parseFloat(e.target.value) || 0)}
                className="sugar-input"
              />
            </div>
          </div>
        </div>

        {/* Panel 3: Metabolic Variables (Model C Context) */}
        <div className="sugar-card space-y-4">
          <div className="card-header flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Flame size={18} style={{ color: '#A9D4E7' }} />
              <h2 className="h2" style={{ fontSize: '1.1rem' }}>
                3. Metabolic Biomarkers (Model C Research)
              </h2>
            </div>
            <span className="badge badge-navy">Exploratory</span>
          </div>

          <p style={{ fontSize: '0.8rem', color: '#80B3D0', margin: 0 }}>
            Metabolic features analyzed in NHANES Model 3 & UCI HCV experiments.
          </p>

          <div className="grid grid-2 gap-3">
            <div>
              <label className="text-white text-xs font-medium block mb-1">Fasting Glucose (mg/dL)</label>
              <input
                type="number"
                min="40"
                max="500"
                value={data.glucose || ''}
                placeholder="Optional"
                onChange={(e) => handleFieldChange('glucose', parseFloat(e.target.value) || undefined)}
                className="sugar-input"
              />
            </div>

            <div>
              <label className="text-white text-xs font-medium block mb-1">Total Cholesterol (mg/dL)</label>
              <input
                type="number"
                min="50"
                max="600"
                value={data.cholesterol || ''}
                placeholder="Optional"
                onChange={(e) => handleFieldChange('cholesterol', parseFloat(e.target.value) || undefined)}
                className="sugar-input"
              />
            </div>
          </div>

          <div>
            <label className="text-white text-xs font-medium block mb-1">
              Liver Steatosis CAP Score (dB/m) [NHANES VCTE]
            </label>
            <input
              type="number"
              min="100"
              max="400"
              value={data.capSteatosis || ''}
              placeholder="e.g. 260 dB/m (Optional)"
              onChange={(e) => handleFieldChange('capSteatosis', parseFloat(e.target.value) || undefined)}
              className="sugar-input"
            />
            <span style={{ fontSize: '0.74rem', color: '#64748b', display: 'block', marginTop: '2px' }}>
              Associated with hepatic steatosis; improved multivariable R² to 13.0% in NHANES analysis.
            </span>
          </div>
        </div>

        {/* Panel 4: Disease Etiology & Stigmata (Model D Planned Context) */}
        <div className="sugar-card space-y-4">
          <div className="card-header flex items-center justify-between">
            <div className="flex items-center gap-2">
              <HelpCircle size={18} style={{ color: '#A9D4E7' }} />
              <h2 className="h2" style={{ fontSize: '1.1rem' }}>
                4. Etiology & Physical Signs (Model D Context)
              </h2>
            </div>
            <span className="badge badge-navy">Planned Pipeline</span>
          </div>

          <p style={{ fontSize: '0.8rem', color: '#80B3D0', margin: 0 }}>
            Etiology context for prospective multi-center pipeline evaluation.
          </p>

          <div>
            <label className="text-white text-xs font-medium block mb-1">Presumed Liver Disease Etiology</label>
            <select
              value={data.etiology || 'other'}
              onChange={(e) => handleFieldChange('etiology', e.target.value)}
              className="sugar-input"
            >
              <option value="hcv">Chronic Hepatitis C (HCV)</option>
              <option value="hbv">Chronic Hepatitis B (HBV)</option>
              <option value="mash">MASH / NAFLD (Metabolic Dysfunction)</option>
              <option value="alcohol">Alcohol-Associated Liver Disease (ALD)</option>
              <option value="cryptogenic">Cryptogenic / Unexplained</option>
              <option value="other">Other / Multi-etiology</option>
            </select>
          </div>

          <div>
            <label className="text-white text-xs font-medium block mb-2">Clinical Physical Signs Observed</label>
            <div className="grid grid-3 gap-2">
              <label className="flex items-center gap-2 text-xs text-secondary cursor-pointer">
                <input
                  type="checkbox"
                  checked={data.ascites || false}
                  onChange={(e) => handleFieldChange('ascites', e.target.checked)}
                />
                <span>Ascites</span>
              </label>

              <label className="flex items-center gap-2 text-xs text-secondary cursor-pointer">
                <input
                  type="checkbox"
                  checked={data.jaundice || false}
                  onChange={(e) => handleFieldChange('jaundice', e.target.checked)}
                />
                <span>Jaundice</span>
              </label>

              <label className="flex items-center gap-2 text-xs text-secondary cursor-pointer">
                <input
                  type="checkbox"
                  checked={data.hepatomegaly || false}
                  onChange={(e) => handleFieldChange('hepatomegaly', e.target.checked)}
                />
                <span>Hepatomegaly</span>
              </label>
            </div>
          </div>
        </div>
      </div>

      {/* Mandatory Doctor Confirmation Bar */}
      <div
        style={{
          background: confirmed ? 'rgba(16, 185, 129, 0.1)' : 'rgba(21, 53, 104, 0.45)',
          border: `1px solid ${confirmed ? 'rgba(52, 211, 153, 0.5)' : 'var(--border-active)'}`,
          borderRadius: '12px',
          padding: '20px',
        }}
        className="space-y-4"
      >
        <label style={{ display: 'flex', alignItems: 'flex-start', gap: '14px', cursor: 'pointer' }}>
          <input
            type="checkbox"
            checked={confirmed}
            onChange={(e) => handleConfirmToggle(e.target.checked)}
            style={{ width: '18px', height: '18px', marginTop: '3px', accentColor: 'var(--ice-blue)' }}
          />
          <div>
            <div style={{ color: '#ffffff', fontWeight: 600, fontSize: '0.98rem' }}>
              Doctor Review & Clinical Verification Confirmation
            </div>
            <p style={{ color: '#cbd5e1', fontSize: '0.85rem', margin: '4px 0 0', lineHeight: 1.45 }}>
              I have reviewed the above laboratory values and confirmed their accuracy against the patient record. I understand this platform calculates the research-informed FIB-4 score and exploratory ML models for clinical decision support, and does not provide an autonomous diagnosis.
            </p>
          </div>
        </label>

        {confirmed && (
          <div className="grid grid-2 gap-4 pt-2 border-t border-[#153568]">
            <div>
              <label className="text-white text-xs font-medium block mb-1">
                Clinician Identifier / License Token:
              </label>
              <input
                type="text"
                value={clinicianId}
                onChange={(e) => setClinicianId(e.target.value)}
                placeholder="e.g. Dr. A. Sharma / Staff Hepatologist"
                className="sugar-input"
                style={{ fontSize: '0.86rem' }}
              />
            </div>
            <div>
              <label className="text-white text-xs font-medium block mb-1">
                Clinician Verification Notes (Optional):
              </label>
              <input
                type="text"
                value={clinicianNotes}
                onChange={(e) => setClinicianNotes(e.target.value)}
                placeholder="e.g. Verified against venous draw at 08:30"
                className="sugar-input"
                style={{ fontSize: '0.86rem' }}
              />
            </div>
          </div>
        )}

        {data.verifiedAt && (
          <div className="flex items-center gap-2 text-xs text-emerald-400">
            <CheckCircle2 size={15} />
            <span>
              Persisted in database as verified by <strong>{data.verifiedBy}</strong> at{' '}
              {new Date(data.verifiedAt).toLocaleTimeString()}
            </span>
          </div>
        )}
      </div>

      {verificationError && (
        <div
          style={{
            background: 'rgba(239, 68, 68, 0.15)',
            border: '1px solid rgba(248, 113, 113, 0.4)',
            borderRadius: '10px',
            padding: '12px 16px',
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
          }}
        >
          <AlertTriangle size={18} className="text-rose-400" />
          <span style={{ color: '#ffffff', fontSize: '0.86rem' }}>
            Verification failed: {verificationError}
          </span>
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
          <span>Back to Report Intake</span>
        </button>

        <button
          type="button"
          onClick={handleNext}
          disabled={!coreInputsValid || !confirmed || isVerifying}
          className="btn btn-primary flex items-center gap-2"
          style={{ padding: '12px 28px', fontSize: '0.95rem' }}
        >
          {isVerifying ? (
            <>
              <Loader2 size={18} className="animate-spin text-ice" />
              <span>Verifying with Database...</span>
            </>
          ) : (
            <>
              <ShieldCheck size={18} />
              <span>Verify & Calculate FIB-4 Score (Step 3)</span>
              <ArrowRight size={18} />
            </>
          )}
        </button>
      </div>
    </div>
  );
};
