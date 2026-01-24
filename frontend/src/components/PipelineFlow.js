import React from 'react';

const steps = [
  { id: 'input', label: 'Call Transcript', icon: '📝' },
  { id: 'qa', label: 'Auto-QA', icon: '🔍' },
  { id: 'decision', label: 'Decision Logic', icon: '🧠' },
  { id: 'twin', label: 'Digital Twin', icon: '🏙️' },
  { id: 'compare', label: 'Comparison', icon: '⚖️' },
  { id: 'insight', label: 'AI Insights', icon: '💡' }
];

const PipelineFlow = ({ currentStep }) => {
  // Simple logic to determine active steps based on currentStep keyword
  // In a real app, we'd pass an index, but we'll approximate for now
  const getStepIndex = (step) => {
    if (!step) return -1;
    if (step === 'complete') return steps.length;
    return steps.findIndex(s => s.id === step);
  };

  const activeIndex = getStepIndex(currentStep);

  return (
    <div className="pipeline-container">
      <div className="pipeline-line"></div>
      {steps.map((step, index) => (
        <div 
          key={step.id} 
          className={`pipeline-step ${index <= activeIndex ? 'active' : ''}`}
        >
          <div className="step-icon">
            {step.icon}
          </div>
          <span className="step-label">{step.label}</span>
        </div>
      ))}
    </div>
  );
};

export default PipelineFlow;
