// SUGAR — Main Assessment Flow Orchestrator (Steps 1–5 Doctor Workflow)
import React, { useState } from 'react';
import { AssessmentStep, ClinicalInputs, PredictionResponse } from '../../types';
import { StepIndicator } from './StepIndicator';
import { ReportUpload } from './ReportUpload';
import { ValueVerification } from './ValueVerification';
import { Fib4Calculator } from './Fib4Calculator';
import { ModelComparison } from './ModelComparison';
import { AssessmentResults } from './AssessmentResults';

const DEFAULT_CLINICAL_DATA: ClinicalInputs = {
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
  reportSource: 'manual',
  verifiedByDoctor: false,
};

interface AssessmentFlowProps {
  onNavigateToResearch: () => void;
}

export const AssessmentFlow: React.FC<AssessmentFlowProps> = ({ onNavigateToResearch }) => {
  const [currentStep, setCurrentStep] = useState<AssessmentStep>(1);
  const [completedSteps, setCompletedSteps] = useState<AssessmentStep[]>([]);
  const [clinicalData, setClinicalData] = useState<ClinicalInputs>(DEFAULT_CLINICAL_DATA);
  const [predictionResult, setPredictionResult] = useState<PredictionResponse | null>(null);

  const markStepCompleted = (step: AssessmentStep) => {
    setCompletedSteps((prev) => (prev.includes(step) ? prev : [...prev, step]));
  };

  const canNavigateTo = (step: AssessmentStep): boolean => {
    if (step === 1) return true;
    if (step === 2) return true;
    if (step === 3) {
      return (
        clinicalData.age > 0 &&
        clinicalData.platelets > 0 &&
        clinicalData.ast > 0 &&
        clinicalData.alt > 0 &&
        clinicalData.verifiedByDoctor
      );
    }
    if (step === 4) return completedSteps.includes(3) || completedSteps.includes(2);
    if (step === 5) return completedSteps.includes(4);
    return false;
  };

  const handleDataLoaded = (
    loadedData: Partial<ClinicalInputs>,
    filename?: string,
    source?: ClinicalInputs['reportSource']
  ) => {
    setClinicalData((prev) => ({
      ...prev,
      ...loadedData,
      reportFilename: filename || prev.reportFilename,
      reportSource: source || prev.reportSource,
      verifiedByDoctor: false, // Must be verified again
    }));
    setPredictionResult(null);
  };

  const handleStep1Proceed = () => {
    markStepCompleted(1);
    setCurrentStep(2);
  };

  const handleStep2Proceed = () => {
    markStepCompleted(2);
    setCurrentStep(3);
  };

  const handleStep3Proceed = () => {
    markStepCompleted(3);
    setCurrentStep(4);
  };

  const handleStep4Proceed = () => {
    markStepCompleted(4);
    setCurrentStep(5);
  };

  const handleReset = () => {
    setCurrentStep(1);
    setCompletedSteps([]);
    setClinicalData(DEFAULT_CLINICAL_DATA);
    setPredictionResult(null);
  };

  return (
    <div className="space-y-4">
      {/* 5-Step Workflow Progression Bar */}
      <StepIndicator
        currentStep={currentStep}
        completedSteps={completedSteps}
        onSelectStep={setCurrentStep}
        canNavigateTo={canNavigateTo}
      />

      {/* Active Step Panel */}
      <div className="sugar-container">
        {currentStep === 1 && (
          <ReportUpload
            existingData={clinicalData}
            onDataLoaded={handleDataLoaded}
            onProceed={handleStep1Proceed}
          />
        )}

        {currentStep === 2 && (
          <ValueVerification
            data={clinicalData}
            onChange={setClinicalData}
            onProceed={handleStep2Proceed}
            onBack={() => setCurrentStep(1)}
          />
        )}

        {currentStep === 3 && (
          <Fib4Calculator
            data={clinicalData}
            onProceed={handleStep3Proceed}
            onBack={() => setCurrentStep(2)}
            onAssessmentCreated={(assessmentId) =>
              setClinicalData((prev) => ({ ...prev, assessmentId }))
            }
          />
        )}

        {currentStep === 4 && (
          <ModelComparison
            data={clinicalData}
            predictionResult={predictionResult}
            onPredictionComplete={setPredictionResult}
            onProceed={handleStep4Proceed}
            onBack={() => setCurrentStep(3)}
          />
        )}

        {currentStep === 5 && (
          <AssessmentResults
            data={clinicalData}
            predictionResult={predictionResult}
            onReset={handleReset}
            onBack={() => setCurrentStep(4)}
            onNavigateToResearch={onNavigateToResearch}
          />
        )}
      </div>
    </div>
  );
};
