import React, { useState, useEffect } from 'react';
import './Feedback.css';

const Feedback = ({ onFeedbackComplete, videoId }) => {
    const [phases, setPhases] = useState([]);
    const [currentIndex, setCurrentIndex] = useState(0);
    const [report, setReport] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [showRefineModal, setShowRefineModal] = useState(false);
    const [userFeedback, setUserFeedback] = useState('');
    const [refining, setRefining] = useState(false);
    const [showKeyframeSelector, setShowKeyframeSelector] = useState(false);
    const [alternativeFrames, setAlternativeFrames] = useState([]);
    const [loadingAlternatives, setLoadingAlternatives] = useState(false);

    const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

    useEffect(() => {
        if (videoId) {
            fetchVLMResults();
        }
    }, [videoId]);

    const fetchVLMResults = async () => {
        try {
            setLoading(true);
            const response = await fetch(`${API_BASE_URL}/api/v1/video/${videoId}/vlm-results`);

            if (response.status === 202) {
                // Still processing, retry after delay
                setTimeout(fetchVLMResults, 2000);
                return;
            }

            if (response.status === 404) {
                // Metadata not created yet, retry after delay
                setTimeout(fetchVLMResults, 2000);
                return;
            }

            if (response.status === 500) {
                // Processing failed
                const errorData = await response.json();
                setError(errorData.error_message || 'VLM processing failed');
                setLoading(false);
                return;
            }

            if (!response.ok) {
                throw new Error('Failed to fetch VLM results');
            }

            const data = await response.json();

            if (data.phases && data.phases.length > 0) {
                // Fetch keyframe images for all phases
                const phasesWithImages = await Promise.all(
                    data.phases.map(async (phase, index) => {
                        try {
                            const frameResponse = await fetch(
                                `${API_BASE_URL}/api/v1/video/${videoId}/phase/${index}/frame`
                            );
                            if (frameResponse.ok) {
                                const frameData = await frameResponse.json();
                                return {
                                    ...phase,
                                    image_base64: frameData.image_base64,
                                    key_timestamp: frameData.timestamp
                                };
                            }
                            return phase;
                        } catch (err) {
                            console.error(`Failed to fetch frame for phase ${index}:`, err);
                            return phase;
                        }
                    })
                );

                setPhases(phasesWithImages);
                setLoading(false);
            } else {
                setError('No phases found in analysis');
                setLoading(false);
            }
        } catch (err) {
            console.error('Error fetching VLM results:', err);
            setError(err.message);
            setLoading(false);
        }
    };

    const handleFeedback = (isCorrect) => {
        if (isCorrect) {
            setReport([...report, phases[currentIndex]]);
            moveToNext();
        } else {
            // Show modal to collect user feedback
            setShowRefineModal(true);
        }
    };

    const moveToNext = () => {
        if (currentIndex < phases.length - 1) {
            setCurrentIndex(currentIndex + 1);
        } else {
            // All phases reviewed, generate final report
            generateFinalReport();
        }
    };

    const handleRefinePhase = async () => {
        if (!userFeedback.trim()) {
            alert('Please provide feedback to help improve the description');
            return;
        }

        setRefining(true);

        try {
            const formData = new FormData();
            formData.append('user_feedback', userFeedback);

            const response = await fetch(
                `${API_BASE_URL}/api/v1/video/${videoId}/phase/${currentIndex}/refine`,
                {
                    method: 'POST',
                    body: formData
                }
            );

            if (!response.ok) {
                throw new Error('Failed to refine phase');
            }

            const data = await response.json();

            // Update the phase with refined description
            const updatedPhases = [...phases];
            updatedPhases[currentIndex] = {
                ...updatedPhases[currentIndex],
                description: data.refined_description,
                refined: true
            };
            setPhases(updatedPhases);

            // Close modal and clear feedback - user will review the refined phase
            setShowRefineModal(false);
            setUserFeedback('');
            setRefining(false);

            // DO NOT move to next - let user review the refined description first

        } catch (err) {
            console.error('Error refining phase:', err);
            alert('Failed to refine phase. Please try again.');
            setRefining(false);
        }
    };

    const handleSkipPhase = () => {
        // Skip this phase without refining
        setShowRefineModal(false);
        setUserFeedback('');
        moveToNext();
    };

    const handleShowKeyframeSelector = async () => {
        setLoadingAlternatives(true);
        setShowKeyframeSelector(true);

        try {
            const response = await fetch(
                `${API_BASE_URL}/api/v1/video/${videoId}/phase/${currentIndex}/alternative-frames`
            );

            if (!response.ok) {
                throw new Error('Failed to load alternative frames');
            }

            const data = await response.json();
            setAlternativeFrames(data.alternative_frames || []);

        } catch (err) {
            console.error('Error loading alternative frames:', err);
            alert('Failed to load alternative frames. Please try again.');
            setShowKeyframeSelector(false);
        } finally {
            setLoadingAlternatives(false);
        }
    };

    const handleSelectAlternativeFrame = async (alternativeFrame) => {
        setLoadingAlternatives(true);  // Show loading state
        try {
            const formData = new FormData();
            formData.append('new_timestamp', alternativeFrame.timestamp_seconds);
            formData.append('new_image_base64', alternativeFrame.image_base64);

            const response = await fetch(
                `${API_BASE_URL}/api/v1/video/${videoId}/phase/${currentIndex}/update-keyframe`,
                {
                    method: 'POST',
                    body: formData
                }
            );

            if (!response.ok) {
                throw new Error('Failed to update keyframe');
            }

            const data = await response.json();

            // Update the current phase with new keyframe AND regenerated description
            const updatedPhases = [...phases];
            updatedPhases[currentIndex] = {
                ...updatedPhases[currentIndex],
                image_base64: alternativeFrame.image_base64,
                key_timestamp: alternativeFrame.timestamp,
                description: data.new_description,  // Update with regenerated description
                description_regenerated: true
            };
            setPhases(updatedPhases);

            // Close the selector
            setShowKeyframeSelector(false);
            setAlternativeFrames([]);
            setLoadingAlternatives(false);

        } catch (err) {
            console.error('Error selecting alternative frame:', err);
            alert('Failed to update keyframe. Please try again.');
            setLoadingAlternatives(false);
        }
    };

    const generateFinalReport = async () => {
        setLoading(true);

        try {
            const response = await fetch(
                `${API_BASE_URL}/api/v1/video/${videoId}/generate-report`,
                {
                    method: 'POST'
                }
            );

            if (!response.ok) {
                throw new Error('Failed to generate report');
            }

            const data = await response.json();

            // Get VLM results to extract latency
            const vlmResponse = await fetch(`${API_BASE_URL}/api/v1/video/${videoId}/vlm-results`);
            let processingLatency = null;
            if (vlmResponse.ok) {
                const vlmData = await vlmResponse.json();
                processingLatency = vlmData.vlm_latency;
            }

            // Pass the final report, phases, and latency to parent
            onFeedbackComplete(data.report, report, processingLatency);

        } catch (err) {
            console.error('Error generating report:', err);
            setError('Failed to generate final report');
            setLoading(false);
        }
    };

    if (!videoId) {
        return (
            <div className="feedback-container">
                <div className="error-state">
                    <p>No video uploaded. Please go back and upload a video.</p>
                </div>
            </div>
        );
    }

    if (loading) {
        return (
            <div className="feedback-container">
                <div className="loading-state">
                    <div className="spinner"></div>
                    <p>Loading surgical phases for review...</p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="feedback-container">
                <div className="error-state">
                    <p>Error: {error}</p>
                    <button onClick={fetchVLMResults}>Retry</button>
                </div>
            </div>
        );
    }

    if (phases.length === 0) {
        return (
            <div className="feedback-container">
                <p>No surgical phases detected</p>
            </div>
        );
    }

    if (currentIndex >= phases.length) {
        return (
            <div className="feedback-container">
                <h2>Thank you for your feedback!</h2>
                <p>Processing your selections...</p>
            </div>
        );
    }

    const currentPhase = phases[currentIndex];

    return (
        <div className="feedback-container">
            <h2>3. Review Surgical Phases</h2>
            <p className="feedback-progress">
                Phase {currentIndex + 1} of {phases.length}
            </p>
            <div className="feedback-card" key={currentIndex}>
                {currentPhase.image_base64 && (
                    <div className="feedback-image-container">
                        <img
                            key={`phase-image-${currentIndex}`}
                            src={`data:image/jpeg;base64,${currentPhase.image_base64}`}
                            alt={`Surgical phase ${currentIndex + 1}`}
                            className="feedback-image"
                        />
                        <div className="timestamp-overlay">
                            {currentPhase.key_timestamp || currentPhase.timestamp || 'N/A'}
                        </div>
                    </div>
                )}
                <div className="feedback-description">
                    <h3>
                        Phase {currentIndex + 1}
                        {currentPhase.refined && (
                            <span className="refined-badge">✓ Refined</span>
                        )}
                    </h3>
                    <p><strong>Time Range:</strong> {currentPhase.timestamp_range || 'N/A'}</p>
                    <p>{currentPhase.description || 'No description available'}</p>
                    {currentPhase.refined && (
                        <div className="refinement-notice">
                            <p className="notice-text">
                                ℹ️ This description has been refined based on your feedback.
                                Review it and click "Correct" to include in the report, or "Needs Refinement" to refine further.
                            </p>
                        </div>
                    )}
                    {currentPhase.description_regenerated && (
                        <div className="refinement-notice">
                            <p className="notice-text">
                                🔄 This description was automatically regenerated based on the new keyframe you selected.
                                Review the updated description and provide your feedback.
                            </p>
                        </div>
                    )}
                </div>
            </div>
            <div className="keyframe-action">
                <button className="change-keyframe-btn" onClick={handleShowKeyframeSelector}>
                    🔄 Change Keyframe (if blurry)
                </button>
            </div>
            <div className="feedback-buttons">
                <button className="incorrect" onClick={() => handleFeedback(false)}>
                    Incorrect - Needs Refinement
                </button>
                <button className="correct" onClick={() => handleFeedback(true)}>
                    Correct - Include in Report
                </button>
            </div>

            {/* Refinement Modal */}
            {showRefineModal && (
                <div className="modal-overlay">
                    <div className="modal-content">
                        <h3>Refine Phase Description</h3>
                        <p className="modal-instruction">
                            Please provide specific feedback to help improve this description:
                        </p>

                        <div className="current-description">
                            <strong>Current Description:</strong>
                            <p>{currentPhase.description || 'No description available'}</p>
                        </div>

                        <div className="feedback-input">
                            <label htmlFor="user-feedback">Your Feedback/Correction:</label>
                            <textarea
                                id="user-feedback"
                                value={userFeedback}
                                onChange={(e) => setUserFeedback(e.target.value)}
                                placeholder="Example: This shows the initial trocar placement at the umbilicus, not gallbladder dissection. The surgeon is using a 12mm trocar with blunt insertion technique..."
                                rows="5"
                                disabled={refining}
                            />
                        </div>

                        <div className="modal-buttons">
                            <button
                                className="cancel-button"
                                onClick={handleSkipPhase}
                                disabled={refining}
                            >
                                Skip This Phase
                            </button>
                            <button
                                className="refine-button"
                                onClick={handleRefinePhase}
                                disabled={refining || !userFeedback.trim()}
                            >
                                {refining ? 'Refining...' : 'Refine Description'}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Keyframe Selector Modal */}
            {showKeyframeSelector && (
                <div className="modal-overlay">
                    <div className="modal-content keyframe-selector-modal">
                        <h3>Select Better Keyframe</h3>
                        <p className="modal-instruction">
                            Choose a clearer image from this phase's time range:
                        </p>

                        {loadingAlternatives ? (
                            <div className="loading-alternatives">
                                <div className="spinner"></div>
                                <p>{alternativeFrames.length > 0 ? 'Regenerating description with new keyframe...' : 'Loading alternative frames...'}</p>
                            </div>
                        ) : (
                            <div className="alternative-frames-grid">
                                {alternativeFrames.map((frame, index) => (
                                    <div
                                        key={index}
                                        className="alternative-frame-item"
                                        onClick={() => handleSelectAlternativeFrame(frame)}
                                    >
                                        <img
                                            src={`data:image/jpeg;base64,${frame.image_base64}`}
                                            alt={`Alternative at ${frame.timestamp}`}
                                        />
                                        <div className="frame-timestamp">{frame.timestamp}</div>
                                    </div>
                                ))}
                            </div>
                        )}

                        <div className="modal-buttons">
                            <button
                                className="cancel-button"
                                onClick={() => {
                                    setShowKeyframeSelector(false);
                                    setAlternativeFrames([]);
                                }}
                            >
                                Cancel
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default Feedback;
