import React from 'react';
import './ProgressTracker.css';

const steps = [
    { name: 'Procedure' },
    { name: 'Upload' },
    { name: 'Feedback' },
    { name: 'Report' }
];

const ProgressTracker = ({ currentStep }) => {
    const getStepClass = (stepIndex) => {
        if (stepIndex + 1 < currentStep) {
            return 'completed';
        }
        if (stepIndex + 1 === currentStep) {
            return 'active';
        }
        return '';
    };

    return (
        <div className="progress-tracker-container">
            {steps.map((step, index) => (
                <React.Fragment key={index}>
                    <div className={`progress-step ${getStepClass(index)}`}>
                        <div className="step-number">{index + 1}</div>
                        <div className="step-name">{step.name}</div>
                    </div>
                    {index < steps.length - 1 && (
                        <div className={`progress-line ${getStepClass(index)}`} />
                    )}
                </React.Fragment>
            ))}
        </div>
    );
};

export default ProgressTracker;
