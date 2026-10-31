// SUGAR — Compact Step Indicator for Doctor Workflow
import React from 'react';
import { CheckCircle2, Circle, FileText, Sliders, Calculator, GitBranch, ClipboardCheck } from 'lucide-react';
import { AssessmentStep } from '../../types';

interface StepIndicatorProps {
  currentStep: AssessmentStep;
  completedSteps: AssessmentStep[];
  onSelectStep: (step: AssessmentStep) => void;
  canNavigateTo: (step: AssessmentStep) => boolean;
}

const STEPS: { step: AssessmentStep; label: string; icon: React.ReactNode; shortDesc: string }[] = [
  { step: 1, label: 'Upload Report', icon: <FileText size={16} />, shortDesc: 'Intake / OCR' },
  { step: 2, label: 'Verify Values', icon: <Sliders size={16} />, shortDesc: 'Review Inputs' },
  { step: 3, label: 'FIB-4 Baseline', icon: <Calculator size={16} />, shortDesc: 'Standard Risk' },
  { step: 4, label: 'Model Pipeline', icon: <GitBranch size={16} />, shortDesc: 'Models A → D' },
  { step: 5, label: 'Clinical Result', icon: <ClipboardCheck size={16} />, shortDesc: 'Unified Report' },
];

export const StepIndicator: React.FC<StepIndicatorProps> = ({
  currentStep,
  completedSteps,
  onSelectStep,
  canNavigateTo,
}) => {
  return (
    <div
      style={{
        background: 'rgba(10, 14, 28, 0.85)',
        border: '1px solid var(--navy-clinical)',
        borderRadius: '12px',
        padding: '12px 20px',
        marginBottom: '24px',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '8px', overflowX: 'auto' }}>
        {STEPS.map((item, index) => {
          const isCurrent = currentStep === item.step;
          const isCompleted = completedSteps.includes(item.step);
          const isAccessible = canNavigateTo(item.step);

          return (
            <React.Fragment key={item.step}>
              <button
                type="button"
                onClick={() => isAccessible && onSelectStep(item.step)}
                disabled={!isAccessible}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '10px',
                  background: isCurrent
                    ? 'rgba(21, 53, 104, 0.7)'
                    : isCompleted
                    ? 'rgba(16, 16, 82, 0.4)'
                    : 'transparent',
                  border: isCurrent
                    ? '1px solid var(--ice-blue)'
                    : isCompleted
                    ? '1px solid rgba(128, 179, 208, 0.35)'
                    : '1px solid transparent',
                  borderRadius: '8px',
                  padding: '8px 14px',
                  cursor: isAccessible ? 'pointer' : 'not-allowed',
                  opacity: isAccessible ? 1 : 0.45,
                  transition: 'all 0.2s ease',
                  textAlign: 'left',
                  flexShrink: 0,
                }}
              >
                <div
                  style={{
                    width: '28px',
                    height: '28px',
                    borderRadius: '50%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    background: isCompleted
                      ? 'var(--success)'
                      : isCurrent
                      ? 'var(--ice-blue)'
                      : 'var(--navy-clinical)',
                    color: isCompleted ? '#070a14' : isCurrent ? '#070a14' : '#80B3D0',
                    fontWeight: 700,
                    fontSize: '0.85rem',
                    fontFamily: 'JetBrains Mono',
                  }}
                >
                  {isCompleted ? <CheckCircle2 size={16} /> : item.step}
                </div>

                <div>
                  <div
                    style={{
                      fontSize: '0.86rem',
                      fontWeight: isCurrent ? 700 : 600,
                      color: isCurrent ? '#ffffff' : isCompleted ? '#cbd5e1' : '#80B3D0',
                      lineHeight: 1.2,
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px',
                    }}
                  >
                    <span>{item.label}</span>
                  </div>
                  <div
                    style={{
                      fontSize: '0.72rem',
                      color: isCurrent ? '#A9D4E7' : '#64748b',
                      marginTop: '2px',
                    }}
                  >
                    {item.shortDesc}
                  </div>
                </div>
              </button>

              {index < STEPS.length - 1 && (
                <div
                  style={{
                    flex: 1,
                    height: '2px',
                    background: completedSteps.includes(item.step)
                      ? 'linear-gradient(90deg, var(--success) 0%, var(--navy-clinical) 100%)'
                      : 'rgba(21, 53, 104, 0.4)',
                    minWidth: '16px',
                    maxWidth: '48px',
                  }}
                />
              )}
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
};
