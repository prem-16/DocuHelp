import React, { useState } from 'react';
import './App.css';
import Logo from './components/Logo';
import ProgressTracker from './components/ProgressTracker';
import ProcedureSelection from './components/ProcedureSelection';
import FileUpload from './components/FileUpload';
import Feedback from './components/Feedback';
import Report from './components/Report';

// API Base URL - configure based on environment
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function App() {
    const [currentStep, setCurrentStep] = useState(1);
    const [selectedProcedure, setSelectedProcedure] = useState(null);
    const [reportData, setReportData] = useState(null);
    const [videoId, setVideoId] = useState(null);
    const [phases, setPhases] = useState([]);
    const [latency, setLatency] = useState(null);

    const handleProcedureSelect = (procedure) => {
        setSelectedProcedure(procedure);
        setCurrentStep(2);
    };

    const handleFilesSelect = async (sopFile, videoFile) => {
        // Validate video file type on frontend
        const validVideoTypes = ['video/mp4', 'video/avi', 'video/mov', 'video/quicktime', 'video/x-msvideo'];
        if (!validVideoTypes.includes(videoFile.type)) {
            alert(`Invalid file type: ${videoFile.type}. Please upload a video file (MP4, AVI, or MOV).`);
            return;
        }

        try {
            // Create FormData to send files
            const formData = new FormData();
            formData.append('video', videoFile);
            formData.append('procedure', selectedProcedure);
            // SOP file removed - no longer accepted by backend

            // Upload to backend API
            const response = await fetch(`${API_BASE_URL}/api/v1/video/upload`, {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ detail: response.statusText }));
                throw new Error(errorData.detail || `Upload failed: ${response.statusText}`);
            }

            const result = await response.json();
            console.log('Upload successful:', result);

            // Store video ID for later use
            setVideoId(result.video_id);

            // Skip analysis step and go directly to feedback
            setCurrentStep(3);

        } catch (error) {
            console.error('Error uploading files:', error);
            alert(`Upload failed: ${error.message}`);
        }
    };

    const handleFeedbackComplete = (report, phasesData, processingLatency) => {
        setReportData(report);
        setPhases(phasesData || []);
        setLatency(processingLatency);
        setCurrentStep(4);
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
                {currentStep === 2 && <FileUpload onFilesSelect={handleFilesSelect} selectedProcedure={selectedProcedure} />}
                {currentStep === 3 && <Feedback onFeedbackComplete={handleFeedbackComplete} videoId={videoId} />}
                {currentStep === 4 && (
                    <Report
                        reportData={reportData}
                        videoId={videoId}
                        procedure={selectedProcedure}
                        phases={phases}
                        latency={latency}
                    />
                )}
            </main>
        </div>
    );
}

export default App;
