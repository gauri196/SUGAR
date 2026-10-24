// SUGAR — Polished Methods & Limitations (Comprehensive Scientific Integrity Documentation)
import React from 'react';
import {
  BookOpen,
  ShieldAlert,
  AlertTriangle,
  FileCheck,
  CheckCircle,
  Scale,
  Microscope,
} from 'lucide-react';

export const MethodsLimitations: React.FC = () => {
  return (
    <div className="space-y-6" style={{ maxWidth: '1080px', margin: '0 auto' }}>
      {/* Header */}
      <div className="flex items-center gap-3 pb-3 border-b border-[#153568]">
        <BookOpen className="text-ice" size={26} />
        <div>
          <h1 className="h1" style={{ fontSize: '1.8rem' }}>
            Methods, Data Provenance & Limitations
          </h1>
          <p className="text-muted mt-1" style={{ fontSize: '0.92rem' }}>
            Formal disclosure of scientific methodologies, epidemiological cohorts, data caveats, and clinical boundaries.
          </p>
        </div>
      </div>

      {/* Prominent Regulatory Notice */}
      <div
        style={{
          background: 'linear-gradient(135deg, rgba(25, 22, 109, 0.45) 0%, rgba(16, 16, 82, 0.7) 100%)',
          border: '1px solid rgba(239, 68, 68, 0.4)',
          borderRadius: '12px',
          padding: '24px',
        }}
        className="space-y-3"
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#FCA5A5', fontWeight: 700, fontSize: '0.95rem', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
          <ShieldAlert size={20} />
          <span>Research Prototype — Non-Diagnostic Designation</span>
        </div>
        <p style={{ fontSize: '0.92rem', color: '#CBD5E1', lineHeight: '1.65', margin: 0 }}>
          The SUGAR platform is an investigational software prototype designed solely for academic research, biomedical education, and machine-learning benchmarking. <strong>It has not been evaluated, cleared, or approved by the United States Food and Drug Administration (FDA), the European Medicines Agency (EMA), or any other regulatory body.</strong> It must not be utilized for diagnosing, staging, treating, or managing liver diseases in patient care. All model outputs are probabilistic research estimations.
        </p>
      </div>

      {/* Methodological Pillars */}
      <div className="grid grid-2 gap-6">
        {/* Pillar 1: Elastography vs. Histology */}
        <div className="sugar-card space-y-3">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#A9D4E7' }}>
            <Microscope size={18} />
            <h3 style={{ fontSize: '1.1rem', color: '#ffffff', margin: 0 }}>1. VCTE Stiffness vs. Biopsy Histology</h3>
          </div>
          <p style={{ fontSize: '0.9rem', color: '#cbd5e1', lineHeight: '1.6' }}>
            A critical scientific distinction is maintained throughout the platform between <strong>Vibration-Controlled Transient Elastography (VCTE)</strong> and <strong>biopsy-confirmed histological staging</strong>:
          </p>
          <ul style={{ paddingLeft: '20px', fontSize: '0.88rem', color: '#80B3D0', lineHeight: '1.55' }} className="space-y-2">
            <li>
              <strong style={{ color: '#ffffff' }}>Transient Elastography:</strong> Measures the physical velocity of low-frequency (50 Hz) mechanical shear waves through liver parenchyma, recorded continuously in kilopascals (kPa).
            </li>
            <li>
              <strong style={{ color: '#ffffff' }}>Confounding Modifiers:</strong> Shear wave velocity is modulated not only by collagen deposition but also by acute inflammation (ALT elevation), biliary cholestasis, cardiac congestion, food intake, and severe steatosis.
            </li>
            <li>
              <strong style={{ color: '#ffffff' }}>Histological Staging (Metavir F0–F4):</strong> Evaluates micro-architectural portal fibrous expansion, bridging, and regenerative nodule formation under microscopy from a needle core biopsy.
            </li>
          </ul>
          <p style={{ fontSize: '0.82rem', color: '#FBBF24', fontStyle: 'italic', borderTop: '1px solid var(--navy-clinical)', paddingTop: '8px', margin: 0 }}>
            Rule: Estimated physical stiffness in kPa must never be reported or interpreted as a confirmed Metavir fibrosis stage.
          </p>
        </div>

        {/* Pillar 2: Egyptian HCV Cohort */}
        <div className="sugar-card space-y-3">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#A9D4E7' }}>
            <Scale size={18} />
            <h3 style={{ fontSize: '1.1rem', color: '#ffffff', margin: 0 }}>2. Egyptian HCV Cohort Feature Definitions</h3>
          </div>
          <p style={{ fontSize: '0.9rem', color: '#cbd5e1', lineHeight: '1.6' }}>
            The machine learning models loaded in <code className="text-ice">backend/main.py</code> were trained on the UCI Egyptian HCV dataset (1,385 patients):
          </p>
          <ul style={{ paddingLeft: '20px', fontSize: '0.88rem', color: '#80B3D0', lineHeight: '1.55' }} className="space-y-2">
            <li>
              <strong style={{ color: '#ffffff' }}>Ratio Variables:</strong> As documented in the repository's <code className="text-ice">models/metrics.json</code>, the variables labeled <code className="text-ice">AST 1</code> and <code className="text-ice">ALT 1</code> represent dataset-specific ratio indices rather than absolute international U/L enzyme levels.
            </li>
            <li>
              <strong style={{ color: '#ffffff' }}>Input Schema Preservation:</strong> The model endpoints expect these exact feature names (<code className="text-ice">AST 1</code>, <code className="text-ice">ALT 1</code>). The Risk Stratification UI preserves these exact feature names while providing realistic input slider ranges.
            </li>
          </ul>
          <p style={{ fontSize: '0.82rem', color: '#A9D4E7', fontStyle: 'italic', borderTop: '1px solid var(--navy-clinical)', paddingTop: '8px', margin: 0 }}>
            This methodological distinction ensures that clinical researchers understand the exploratory nature of the trained scikit-learn weights.
          </p>
        </div>

        {/* Pillar 3: Class Imbalance */}
        <div className="sugar-card space-y-3">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#A9D4E7' }}>
            <AlertTriangle size={18} />
            <h3 style={{ fontSize: '1.1rem', color: '#ffffff', margin: 0 }}>3. Class Imbalance & Diagnostic Tradeoffs</h3>
          </div>
          <p style={{ fontSize: '0.9rem', color: '#cbd5e1', lineHeight: '1.6' }}>
            The platform openly reports full diagnostic matrices (sensitivity, specificity, precision, ROC-AUC) rather than presenting misleading raw accuracy figures:
          </p>
          <ul style={{ paddingLeft: '20px', fontSize: '0.88rem', color: '#80B3D0', lineHeight: '1.55' }} className="space-y-2">
            <li>
              In <strong>Target A (Stage 1 vs. 2–4)</strong>, the Expanded Random Forest yields 64.5% overall accuracy and 78.5% sensitivity, but specificity drops to 20.6% and ROC-AUC is 0.475.
            </li>
            <li>
              This behavior occurs because the cohort contains predominantly intermediate-to-advanced patients, causing classifiers to overpredict positive risk without acquiring genuine discriminatory boundaries.
            </li>
            <li>
              In <strong>4-Stage Multiclass classification</strong>, all evaluated algorithms perform at ~24–27%, which is statistically indistinguishable from a random 25% chance baseline.
            </li>
          </ul>
        </div>

        {/* Pillar 4: NHANES Methodology */}
        <div className="sugar-card space-y-3">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#A9D4E7' }}>
            <FileCheck size={18} />
            <h3 style={{ fontSize: '1.1rem', color: '#ffffff', margin: 0 }}>4. NHANES 2017–2020 Study Cohort Criteria</h3>
          </div>
          <p style={{ fontSize: '0.9rem', color: '#cbd5e1', lineHeight: '1.6' }}>
            The epidemiological analysis in the Research Lab is derived directly from complete exams in the pre-pandemic cycle:
          </p>
          <ul style={{ paddingLeft: '20px', fontSize: '0.88rem', color: '#80B3D0', lineHeight: '1.55' }} className="space-y-2">
            <li>
              <strong style={{ color: '#ffffff' }}>Sample Size:</strong> 7,211 adults (age ≥18) who completed liver ultrasound transient elastography exams meeting CDC/NCHS reliability criteria (≥10 valid stiffness measures, stiffness IQR / median ≤30%).
            </li>
            <li>
              <strong style={{ color: '#ffffff' }}>Data Files:</strong> Merged from <code className="text-ice">P_DEMO.xpt</code> (demographics), <code className="text-ice">P_BIOPRO.xpt</code> (biochemistry), <code className="text-ice">P_CBC.xpt</code> (blood counts), and <code className="text-ice">P_LUX.xpt</code> (liver examination).
            </li>
            <li>
              <strong style={{ color: '#ffffff' }}>Holdout Split:</strong> Standardized evaluation across 5,768 training and 1,442 test participants.
            </li>
          </ul>
        </div>
      </div>

      {/* Summary Footer */}
      <div className="sugar-card" style={{ padding: '16px 20px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.88rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#CBD5E1' }}>
          <CheckCircle size={18} style={{ color: '#A9D4E7' }} />
          <span>SUGAR adheres to STARD and TRIPOD reporting guidelines for diagnostic and predictive models.</span>
        </div>
        <span className="badge badge-navy">SUGAR Scientific Governance</span>
      </div>
    </div>
  );
};
