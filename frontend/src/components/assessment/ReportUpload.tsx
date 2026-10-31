// SUGAR — Step 1: Laboratory Report Intake & Extraction Layer
import React, { useState, useRef } from 'react';
import {
  UploadCloud,
  AlertCircle,
  CheckCircle2,
  ArrowRight,
  Sparkles,
  Edit3,
  Loader2,
  FileCheck,
  Info,
} from 'lucide-react';
import { ClinicalInputs, ExtractionResponse } from '../../types';
import {
  extractReport,
  registerReport,
  clinicalInputsToObservationPayload,
} from '../../services/api';

interface ReportUploadProps {
  onDataLoaded: (
    data: Partial<ClinicalInputs>,
    filename?: string,
    source?: ClinicalInputs['reportSource']
  ) => void;
  onProceed: () => void;
  existingData: ClinicalInputs;
}

interface SampleReport {
  id: string;
  name: string;
  patientProfile: string;
  indication: string;
  values: Partial<ClinicalInputs>;
  rawSnippet: string;
}

const SAMPLE_REPORTS: SampleReport[] = [
  {
    id: 'case_1',
    name: 'Case 1: Routine Metabolic Health Screen',
    patientProfile: '42yo Male | Asymptomatic | Annual Physical',
    indication: 'Routine wellness panel. Normal transaminases and platelet count.',
    values: {
      age: 42,
      bmi: 24.5,
      platelets: 255,
      ast: 25,
      alt: 24,
      wbc: 6.5,
      rbc: 4.8,
      hgb: 15.0,
      glucose: 92,
      cholesterol: 185,
      capSteatosis: 210,
      etiology: 'mash',
      ascites: false,
      jaundice: false,
      hepatomegaly: false,
    },
    rawSnippet: `REPORT TYPE: Comprehensive Metabolic & Hematology Panel
PATIENT: Anonymous Subject 1042 | AGE: 42 | SEX: Male
LAB FINDINGS:
  - Platelet Count: 255 x10^3/uL (Ref: 150-450)
  - AST (SGOT): 25 U/L (Ref: 10-40)
  - ALT (SGPT): 24 U/L (Ref: 7-56)
  - BMI: 24.5 kg/m^2
  - WBC: 6.5 x10^3/uL | RBC: 4.80 x10^6/uL | Hgb: 15.0 g/dL`,
  },
  {
    id: 'case_2',
    name: 'Case 2: Indeterminate Transaminitis Panel',
    patientProfile: '56yo Female | Overweight | Borderline Thrombocytes',
    indication: 'Mild asymptomatic aminotransferase elevation with moderate thrombocytopenia.',
    values: {
      age: 56,
      bmi: 29.4,
      platelets: 145,
      ast: 58,
      alt: 48,
      wbc: 8.2,
      rbc: 4.3,
      hgb: 13.6,
      glucose: 114,
      cholesterol: 235,
      capSteatosis: 275,
      etiology: 'mash',
      ascites: false,
      jaundice: false,
      hepatomegaly: false,
    },
    rawSnippet: `REPORT TYPE: Liver Function & CBC Profile
PATIENT: Anonymous Subject 2056 | AGE: 56 | SEX: Female
LAB FINDINGS:
  - Platelet Count: 145 x10^3/uL [Low/Borderline]
  - AST (SGOT): 58 U/L [Elevated]
  - ALT (SGPT): 48 U/L [Elevated]
  - BMI: 29.4 kg/m^2 | Fasting Glucose: 114 mg/dL
  - WBC: 8.2 x10^3/uL | RBC: 4.30 x10^6/uL | Hgb: 13.6 g/dL`,
  },
  {
    id: 'case_3',
    name: 'Case 3: Chronic Viral Hepatitis / Advanced Risk',
    patientProfile: '64yo Male | Chronic HCV History | Thrombocytopenia',
    indication: 'Significant platelet drop with inverted AST/ALT ratio suggesting advanced fibrosis.',
    values: {
      age: 64,
      bmi: 32.8,
      platelets: 92,
      ast: 98,
      alt: 65,
      wbc: 10.4,
      rbc: 3.9,
      hgb: 12.1,
      glucose: 142,
      cholesterol: 210,
      capSteatosis: 310,
      etiology: 'hcv',
      ascites: false,
      jaundice: true,
      hepatomegaly: true,
    },
    rawSnippet: `REPORT TYPE: Hepatology Specialized Diagnostic Panel
PATIENT: Anonymous Subject 3064 | AGE: 64 | SEX: Male
LAB FINDINGS:
  - Platelet Count: 92 x10^3/uL [Thrombocytopenia]
  - AST (SGOT): 98 U/L [Elevated AST > ALT]
  - ALT (SGPT): 65 U/L [Elevated]
  - BMI: 32.8 kg/m^2 | Clinical: Mild scleral jaundice
  - WBC: 10.4 x10^3/uL | RBC: 3.90 x10^6/uL | Hgb: 12.1 g/dL`,
  },
];

export const ReportUpload: React.FC<ReportUploadProps> = ({
  onDataLoaded,
  onProceed,
  existingData,
}) => {
  const [dragActive, setDragActive] = useState<boolean>(false);
  const [selectedCaseId, setSelectedCaseId] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [extractionResult, setExtractionResult] = useState<ExtractionResponse | null>(null);
  const [statusMessage, setStatusMessage] = useState<{
    type: 'info' | 'success' | 'warning' | 'error';
    title: string;
    description: string;
  } | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const processUploadedFile = async (file: File) => {
    setSelectedCaseId(null);

    // Enforce 5MB upload limit
    if (file.size > 5 * 1024 * 1024) {
      setStatusMessage({
        type: 'error',
        title: 'File Size Limit Exceeded',
        description: `File size is ${(file.size / (1024 * 1024)).toFixed(2)} MB. Maximum allowed size is 5.0 MB.`,
      });
      return;
    }

    setIsProcessing(true);
    setStatusMessage({
      type: 'info',
      title: 'Extracting Medical Report',
      description: `Sending "${file.name}" to verified backend report extraction service...`,
    });

    try {
      // 1. Call Phase 4 Extraction API
      const extraction = await extractReport(file);
      setExtractionResult(extraction);

      if (extraction.extraction_status === 'no_text_found') {
        setStatusMessage({
          type: 'warning',
          title: 'Scanned Document / No Digital Text Found',
          description:
            `Uploaded file "${file.name}" contains no extractable digital text. Vision/OCR processing is not configured in this build. SUGAR does not fabricate OCR extractions. Please review and input values directly in Step 2.`,
        });
        setIsProcessing(false);
        return;
      }

      if (!extraction.success || extraction.extraction_status === 'failed') {
        const errorText = extraction.errors.length > 0 ? extraction.errors.join('; ') : 'Document parsing failed.';
        setStatusMessage({
          type: 'error',
          title: 'Extraction Failed',
          description: errorText,
        });
        setIsProcessing(false);
        return;
      }

      // Map canonical values from backend
      const vals = extraction.clinical_values;
      const mappedData: Partial<ClinicalInputs> = {};
      if (vals.age !== null && vals.age !== undefined) mappedData.age = vals.age;
      if (vals.bmi !== null && vals.bmi !== undefined) mappedData.bmi = vals.bmi;
      if (vals.platelets !== null && vals.platelets !== undefined) mappedData.platelets = vals.platelets;
      if (vals.ast !== null && vals.ast !== undefined) mappedData.ast = vals.ast;
      if (vals.alt !== null && vals.alt !== undefined) mappedData.alt = vals.alt;
      if (vals.wbc !== null && vals.wbc !== undefined) mappedData.wbc = vals.wbc;
      if (vals.rbc !== null && vals.rbc !== undefined) mappedData.rbc = vals.rbc;
      if (vals.hgb !== null && vals.hgb !== undefined) mappedData.hgb = vals.hgb;
      if (vals.glucose !== null && vals.glucose !== undefined) mappedData.glucose = vals.glucose;
      if (vals.cholesterol !== null && vals.cholesterol !== undefined) mappedData.cholesterol = vals.cholesterol;
      if (vals.cap_steatosis !== null && vals.cap_steatosis !== undefined) mappedData.capSteatosis = vals.cap_steatosis;

      // 2. Register report and unverified observation in database
      const fileExt = file.name.split('.').pop()?.toLowerCase();
      const reportSource: ClinicalInputs['reportSource'] =
        fileExt === 'json' ? 'json' : fileExt === 'csv' ? 'csv' : fileExt === 'pdf' ? 'pdf' : 'manual';

      const regResponse = await registerReport({
        original_filename: file.name,
        media_type: extraction.media_type,
        file_size_bytes: file.size,
        extraction_status: extraction.extraction_status,
        clinical_values: clinicalInputsToObservationPayload({
          ...existingData,
          ...mappedData,
        }),
        field_provenance_json: JSON.stringify(extraction.extracted_fields),
        uploaded_by: 'doctor_frontend_user',
      });

      onDataLoaded(
        {
          ...mappedData,
          reportId: regResponse.report_id,
          patientId: regResponse.patient_id,
          observationId: regResponse.observation_id,
          extractedFields: extraction.extracted_fields,
          reportFilename: file.name,
          reportSource,
          verifiedByDoctor: false,
        },
        file.name,
        reportSource
      );

      const fieldCount = Object.keys(extraction.extracted_fields).length;
      setStatusMessage({
        type: 'success',
        title: `Report Extracted & Registered (${extraction.extraction_status.toUpperCase()})`,
        description: `Successfully extracted ${fieldCount} fields (Report ID: ${regResponse.report_id.slice(0, 8)}...). Values marked unverified pending clinician confirmation in Step 2.`,
      });
    } catch (err: any) {
      setStatusMessage({
        type: 'error',
        title: 'Backend Processing Error',
        description: err?.message || 'Could not connect to backend extraction service.',
      });
    } finally {
      setIsProcessing(false);
    }
  };

  const handleFileDrop = (file: File) => {
    processUploadedFile(file);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileDrop(e.dataTransfer.files[0]);
    }
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      handleFileDrop(e.target.files[0]);
    }
  };

  const handleSelectCase = async (caseItem: SampleReport) => {
    setSelectedCaseId(caseItem.id);
    setIsProcessing(true);
    setStatusMessage({
      type: 'info',
      title: `Registering Cohort Case: ${caseItem.name}`,
      description: 'Creating patient encounter and unverified observation in database...',
    });

    try {
      const regResponse = await registerReport({
        external_subject_id: `SUGAR-SAMPLE-${caseItem.id}`,
        original_filename: `${caseItem.id}.lab_report`,
        media_type: 'application/json',
        file_size_bytes: caseItem.rawSnippet.length,
        extraction_status: 'parsed',
        clinical_values: clinicalInputsToObservationPayload(caseItem.values),
        uploaded_by: 'sample_cohort_selector',
      });

      onDataLoaded(
        {
          ...caseItem.values,
          reportId: regResponse.report_id,
          patientId: regResponse.patient_id,
          observationId: regResponse.observation_id,
          reportFilename: `${caseItem.id}.lab_report`,
          reportSource: 'sample',
          verifiedByDoctor: false,
        },
        `${caseItem.id}.lab_report`,
        'sample'
      );

      setStatusMessage({
        type: 'success',
        title: `Loaded ${caseItem.name}`,
        description: `Encounter registered (Patient ID: ${regResponse.patient_id.slice(0, 8)}...). Proceed to Step 2 to verify values.`,
      });
    } catch (err: any) {
      // Fallback in case backend is offline
      onDataLoaded(caseItem.values, `${caseItem.id}.lab_report`, 'sample');
      setStatusMessage({
        type: 'info',
        title: `Loaded ${caseItem.name} (Local Preview)`,
        description: `Pre-populated laboratory values (${caseItem.patientProfile}). Backend offline or error: ${err.message}`,
      });
    } finally {
      setIsProcessing(false);
    }
  };

  const handleManualProceed = async () => {
    if (!existingData.observationId) {
      setIsProcessing(true);
      try {
        const regResponse = await registerReport({
          original_filename: 'manual_intake_report.json',
          media_type: 'application/json',
          extraction_status: 'parsed',
          clinical_values: clinicalInputsToObservationPayload(existingData),
          uploaded_by: 'manual_intake_user',
        });
        onDataLoaded(
          {
            reportId: regResponse.report_id,
            patientId: regResponse.patient_id,
            observationId: regResponse.observation_id,
            reportSource: 'manual',
            reportFilename: 'manual_intake_report.json',
          },
          'manual_intake_report.json',
          'manual'
        );
      } catch (err) {
        console.warn('Manual intake registration deferred:', err);
      } finally {
        setIsProcessing(false);
      }
    }
    onProceed();
  };

  return (
    <div className="space-y-6">
      {/* Step Header */}
      <div className="border-b border-[#153568] pb-4">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <div>
            <span className="badge badge-ice mb-2">Step 1 of 5</span>
            <h1 className="h1 flex items-center gap-2">
              <UploadCloud className="text-ice" size={26} />
              Patient Laboratory Report Intake
            </h1>
          </div>
          <button
            type="button"
            onClick={handleManualProceed}
            disabled={isProcessing}
            className="btn btn-secondary flex items-center gap-2"
          >
            <Edit3 size={16} />
            <span>Skip to Manual Entry & Verification</span>
            <ArrowRight size={16} />
          </button>
        </div>
        <p className="text-muted mt-2" style={{ fontSize: '0.92rem' }}>
          Upload a structured patient lab report (.csv, .json, .pdf), select a standardized medical research case, or enter clinical parameters directly.
        </p>
      </div>

      {/* Prominent Upload Dropzone */}
      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => !isProcessing && fileInputRef.current?.click()}
        style={{
          border: `2px dashed ${dragActive ? 'var(--ice-blue)' : 'var(--navy-clinical)'}`,
          background: dragActive ? 'rgba(21, 53, 104, 0.45)' : 'rgba(10, 14, 28, 0.75)',
          borderRadius: '16px',
          padding: '44px 24px',
          textAlign: 'center',
          cursor: isProcessing ? 'wait' : 'pointer',
          transition: 'all 0.25s ease',
          opacity: isProcessing ? 0.7 : 1,
        }}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv,.json,.txt,.pdf"
          style={{ display: 'none' }}
          onChange={handleFileInputChange}
          disabled={isProcessing}
        />

        {isProcessing ? (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '12px' }}>
            <Loader2 size={40} className="text-ice animate-spin" />
            <h3 style={{ fontSize: '1.15rem', color: '#ffffff', margin: 0 }}>
              Analyzing & Extracting Medical Report...
            </h3>
            <p style={{ color: '#80B3D0', fontSize: '0.86rem', margin: 0 }}>
              Parsing clinical biomarkers and creating unverified encounter record...
            </p>
          </div>
        ) : (
          <>
            <div
              style={{
                width: '64px',
                height: '64px',
                borderRadius: '50%',
                background: 'rgba(21, 53, 104, 0.6)',
                border: '1px solid var(--ice-blue)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                margin: '0 auto 16px',
                color: 'var(--ice-blue)',
              }}
            >
              <UploadCloud size={32} />
            </div>

            <h3 style={{ fontSize: '1.2rem', color: '#ffffff', marginBottom: '8px' }}>
              Drag and drop patient laboratory report here
            </h3>
            <p style={{ color: '#80B3D0', fontSize: '0.88rem', maxWidth: '540px', margin: '0 auto 16px' }}>
              Supports structured lab exports (<strong>.csv</strong>, <strong>.json</strong>) and digital <strong>.pdf</strong> clinical reports (max 5 MB).
            </p>

            <div style={{ display: 'flex', justifyContent: 'center', gap: '12px', flexWrap: 'wrap' }}>
              <span className="badge badge-navy">.CSV / .JSON / .PDF</span>
              <span className="badge badge-navy">SHA-256 Deduplication</span>
              <span className="badge badge-ice">Database Intake Gated</span>
            </div>
          </>
        )}
      </div>

      {/* Extraction Provenance & Human Verification Notice */}
      {extractionResult && extractionResult.success && (
        <div
          style={{
            background: 'rgba(21, 53, 104, 0.35)',
            border: '1px solid var(--ice-blue)',
            borderRadius: '10px',
            padding: '16px 20px',
          }}
          className="space-y-3"
        >
          <div className="flex items-center justify-between flex-wrap gap-2">
            <div className="flex items-center gap-2">
              <FileCheck size={18} className="text-emerald-400" />
              <h4 style={{ color: '#ffffff', margin: 0, fontSize: '0.94rem' }}>
                Extracted Biomarkers Provenance ({extractionResult.filename})
              </h4>
            </div>
            <span className="badge badge-warning">Unverified Automated Extraction</span>
          </div>

          <p style={{ fontSize: '0.82rem', color: '#cbd5e1', margin: 0, lineHeight: 1.45 }}>
            {extractionResult.verification_disclaimer}
          </p>

          <div className="flex flex-wrap gap-2 pt-1">
            {Object.entries(extractionResult.extracted_fields).map(([name, field]) => (
              <span
                key={name}
                className="badge badge-navy"
                style={{ fontSize: '0.74rem', fontFamily: 'JetBrains Mono' }}
              >
                {name.toUpperCase()}: {field.interpreted_value ?? 'N/A'}{' '}
                {field.unit ? `(${field.unit})` : ''} [{field.status}]
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Honest Diagnostic Feedback Alert */}
      {statusMessage && (
        <div
          style={{
            borderRadius: '10px',
            padding: '16px 20px',
            border: '1px solid',
            background:
              statusMessage.type === 'success'
                ? 'rgba(16, 185, 129, 0.12)'
                : statusMessage.type === 'warning'
                ? 'rgba(245, 158, 11, 0.12)'
                : statusMessage.type === 'error'
                ? 'rgba(239, 68, 68, 0.12)'
                : 'rgba(21, 53, 104, 0.5)',
            borderColor:
              statusMessage.type === 'success'
                ? 'rgba(52, 211, 153, 0.4)'
                : statusMessage.type === 'warning'
                ? 'rgba(251, 191, 36, 0.4)'
                : statusMessage.type === 'error'
                ? 'rgba(248, 113, 113, 0.4)'
                : 'var(--ice-blue)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
            {statusMessage.type === 'success' ? (
              <CheckCircle2 size={20} className="text-emerald-400" style={{ flexShrink: 0, marginTop: '2px' }} />
            ) : statusMessage.type === 'warning' ? (
              <AlertCircle size={20} className="text-amber-300" style={{ flexShrink: 0, marginTop: '2px' }} />
            ) : (
              <Info size={20} className="text-ice" style={{ flexShrink: 0, marginTop: '2px' }} />
            )}
            <div>
              <h4 style={{ color: '#ffffff', fontSize: '0.96rem', margin: 0, textTransform: 'none', letterSpacing: 'normal' }}>
                {statusMessage.title}
              </h4>
              <p style={{ color: '#cbd5e1', fontSize: '0.86rem', margin: '4px 0 0', lineHeight: 1.5 }}>
                {statusMessage.description}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Standardized Test Cohort Patient Cases */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Sparkles size={18} style={{ color: '#A9D4E7' }} />
            <h3 style={{ fontSize: '1.05rem', color: '#ffffff', margin: 0 }}>
              Or Load a Verified Laboratory Cohort Case
            </h3>
          </div>
          <span style={{ fontSize: '0.8rem', color: '#80B3D0' }}>
            Instant end-to-end evaluation with clinical presets
          </span>
        </div>

        <div className="grid grid-3 gap-4">
          {SAMPLE_REPORTS.map((item) => {
            const isSelected = selectedCaseId === item.id;
            return (
              <div
                key={item.id}
                onClick={() => handleSelectCase(item)}
                style={{
                  background: isSelected ? 'rgba(21, 53, 104, 0.65)' : 'rgba(10, 14, 28, 0.85)',
                  border: isSelected ? '1px solid var(--ice-blue)' : '1px solid var(--navy-clinical)',
                  borderRadius: '10px',
                  padding: '16px',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                }}
              >
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="badge badge-navy" style={{ fontSize: '0.72rem' }}>
                      {item.id.replace('_', ' ').toUpperCase()}
                    </span>
                    {isSelected && <CheckCircle2 size={16} className="text-ice" />}
                  </div>
                  <h4 style={{ color: '#ffffff', fontSize: '0.95rem', margin: '0 0 4px', textTransform: 'none' }}>
                    {item.name}
                  </h4>
                  <p style={{ fontSize: '0.8rem', color: '#A9D4E7', marginBottom: '8px', fontWeight: 500 }}>
                    {item.patientProfile}
                  </p>
                  <p style={{ fontSize: '0.78rem', color: '#80B3D0', lineHeight: 1.45, margin: 0 }}>
                    {item.indication}
                  </p>
                </div>

                <div style={{ marginTop: '14px', paddingTop: '10px', borderTop: '1px solid rgba(21, 53, 104, 0.6)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '0.75rem', fontFamily: 'JetBrains Mono', color: '#cbd5e1' }}>
                    Plat: {item.values.platelets}k | AST: {item.values.ast} | ALT: {item.values.alt}
                  </span>
                  <span style={{ fontSize: '0.78rem', color: isSelected ? '#A9D4E7' : '#80B3D0', fontWeight: 600 }}>
                    {isSelected ? 'Loaded' : 'Select'}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Step Navigation Actions */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          paddingTop: '16px',
          borderTop: '1px solid var(--navy-clinical)',
        }}
      >
        <div style={{ fontSize: '0.82rem', color: '#80B3D0' }}>
          Current Source:{' '}
          <span style={{ color: '#ffffff', fontFamily: 'JetBrains Mono' }}>
            {existingData.reportSource ? existingData.reportSource.toUpperCase() : 'MANUAL ENTRY'}
          </span>
          {existingData.reportFilename && ` (${existingData.reportFilename})`}
        </div>

        <button
          type="button"
          onClick={handleManualProceed}
          disabled={isProcessing}
          className="btn btn-primary flex items-center gap-2"
          style={{ padding: '12px 28px', fontSize: '0.95rem' }}
        >
          <span>Continue to Step 2: Verify & Edit Clinical Variables</span>
          <ArrowRight size={18} />
        </button>
      </div>
    </div>
  );
};
