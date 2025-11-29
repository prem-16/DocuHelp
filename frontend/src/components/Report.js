import React, { useState, useEffect } from 'react';
import './Report.css';

const Report = ({ reportData, videoId, procedure, phases, latency }) => {
    const [accuracyScore, setAccuracyScore] = useState(null);
    const [evaluating, setEvaluating] = useState(false);
    const [evaluationDetails, setEvaluationDetails] = useState(null);

    const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

    useEffect(() => {
        // Auto-evaluate on mount
        if (reportData && !accuracyScore) {
            evaluateReport();
        }
    }, [reportData]);

    const evaluateReport = async () => {
        setEvaluating(true);
        try {
            const response = await fetch(`${API_BASE_URL}/api/v1/report/evaluate`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    report: reportData,
                    procedure: procedure,
                    phases_count: phases?.length || 0
                })
            });

            if (!response.ok) {
                throw new Error('Evaluation failed');
            }

            const data = await response.json();
            setAccuracyScore(data.accuracy_score);
            setEvaluationDetails(data.evaluation_details);
        } catch (error) {
            console.error('Error evaluating report:', error);
        } finally {
            setEvaluating(false);
        }
    };

    const downloadReport = () => {
        const blob = new Blob([reportData], { type: 'text/plain' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `surgical_report_${videoId || 'document'}.txt`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    };

    const getScoreColor = (score) => {
        if (score >= 90) return '#4caf50'; // Green
        if (score >= 80) return '#8bc34a'; // Light green
        if (score >= 70) return '#ffc107'; // Yellow
        if (score >= 60) return '#ff9800'; // Orange
        return '#f44336'; // Red
    };

    return (
        <div className="report-container">
            <h2>4. Final Surgical Report</h2>

            {/* Metadata Section */}
            <div className="report-metadata">
                <div className="metadata-item">
                    <strong>Procedure:</strong> {procedure || 'N/A'}
                </div>
                <div className="metadata-item">
                    <strong>Phases Analyzed:</strong> {phases?.length || 'N/A'}
                </div>
                <div className="metadata-item">
                    <strong>Processing Time:</strong> {latency ? `${latency}s` : 'N/A'}
                </div>
            </div>

            {/* Accuracy Score */}
            {evaluating && (
                <div className="evaluation-loading">
                    <div className="spinner-small"></div>
                    <span>Evaluating report quality...</span>
                </div>
            )}

            {accuracyScore !== null && (
                <div className="accuracy-section">
                    <h3>Quality Assessment</h3>
                    <div className="accuracy-score" style={{ borderColor: getScoreColor(accuracyScore) }}>
                        <div className="score-circle" style={{ backgroundColor: getScoreColor(accuracyScore) }}>
                            {accuracyScore}%
                        </div>
                        <div className="score-label">Accuracy Score</div>
                    </div>
                    {evaluationDetails && (
                        <div className="evaluation-details">
                            <h4>Evaluation Criteria:</h4>
                            <ul>
                                {evaluationDetails.completeness && (
                                    <li><strong>Completeness:</strong> {evaluationDetails.completeness}</li>
                                )}
                                {evaluationDetails.chronological_order && (
                                    <li><strong>Chronological Order:</strong> {evaluationDetails.chronological_order}</li>
                                )}
                                {evaluationDetails.clinical_accuracy && (
                                    <li><strong>Clinical Accuracy:</strong> {evaluationDetails.clinical_accuracy}</li>
                                )}
                                {evaluationDetails.terminology && (
                                    <li><strong>Medical Terminology:</strong> {evaluationDetails.terminology}</li>
                                )}
                            </ul>
                        </div>
                    )}
                </div>
            )}

            {/* Report Content */}
            <div className="report-content">
                <pre>{reportData || 'No report generated'}</pre>
            </div>

            {/* Action Buttons */}
            <div className="report-actions">
                <button className="download-button" onClick={downloadReport}>
                    Download Report
                </button>
                {!evaluating && !accuracyScore && (
                    <button className="evaluate-button" onClick={evaluateReport}>
                        Evaluate Report Quality
                    </button>
                )}
                <button className="new-analysis-button" onClick={() => window.location.reload()}>
                    New Analysis
                </button>
            </div>
        </div>
    );
};

export default Report;
