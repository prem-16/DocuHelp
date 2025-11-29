import React, { useState } from 'react';
import './App.css';
import Logo from './components/Logo';
import ProgressTracker from './components/ProgressTracker';
import ProcedureSelection from './components/ProcedureSelection';
import FileUpload from './components/FileUpload';
import VideoAnalysis from './components/VideoAnalysis';
import Feedback from './components/Feedback';
import Report from './components/Report';

function App() {
    const [currentStep, setCurrentStep] = useState(1);
    const [selectedProcedure, setSelectedProcedure] = useState(null);
    const [reportData, setReportData] = useState([]);

    const handleProcedureSelect = (procedure) => {
        setSelectedProcedure(procedure);
        setCurrentStep(2);
    };

    const handleFilesSelect = (sopFile, videoFile) => {
        setCurrentStep(3);
        // Simulate analysis time
        setTimeout(() => {
            setCurrentStep(4);
        }, 3000);
    };

    const handleFeedbackComplete = (report) => {
        setReportData(report);
        setCurrentStep(5);
    };

    return (
        <div className="App">
            <header className="App-header">
                <Logo />
                <h1>Surgery Analysis Report Generator</h1>
            </header>
            <ProgressTracker currentStep={currentStep} />
            <main>
                {currentStep === 1 && <ProcedureSelection onProcedureSelect={handleProcedureSelect} />}
                {currentStep === 2 && <FileUpload onFilesSelect={handleFilesSelect} />}
                {currentStep === 3 && <VideoAnalysis />}
                {currentStep === 4 && <Feedback onFeedbackComplete={handleFeedbackComplete} />}
                {currentStep === 5 && <Report reportData={reportData} />}
            </main>
        </div>
    );
}

export default App;
