import React, { useState, useEffect, useRef } from 'react';
import './KeyframeSwiper.css';

const KeyframeSwiper = ({ videoId, onComplete }) => {
    const [phases, setPhases] = useState([]);
    const [currentIndex, setCurrentIndex] = useState(0);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [touchStart, setTouchStart] = useState(0);
    const [touchEnd, setTouchEnd] = useState(0);
    const [isDragging, setIsDragging] = useState(false);
    const [dragOffset, setDragOffset] = useState(0);
    const [isTransitioning, setIsTransitioning] = useState(false);

    const containerRef = useRef(null);
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
                                    timestamp: frameData.timestamp
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

    const handleTouchStart = (e) => {
        setTouchStart(e.targetTouches[0].clientX);
        setIsDragging(true);
    };

    const handleTouchMove = (e) => {
        if (!isDragging) return;
        const currentTouch = e.targetTouches[0].clientX;
        const diff = currentTouch - touchStart;
        setDragOffset(diff);
        setTouchEnd(currentTouch);
    };

    const handleTouchEnd = () => {
        if (!isDragging) return;
        setIsDragging(false);
        const swipeThreshold = 50;

        if (touchStart - touchEnd > swipeThreshold) {
            // Swiped left - next
            handleNext();
        } else if (touchEnd - touchStart > swipeThreshold) {
            // Swiped right - previous
            handlePrevious();
        }

        setDragOffset(0);
    };

    const handleMouseDown = (e) => {
        setTouchStart(e.clientX);
        setIsDragging(true);
    };

    const handleMouseMove = (e) => {
        if (!isDragging) return;
        const diff = e.clientX - touchStart;
        setDragOffset(diff);
        setTouchEnd(e.clientX);
    };

    const handleMouseUp = () => {
        if (!isDragging) return;
        setIsDragging(false);
        const swipeThreshold = 50;

        if (touchStart - touchEnd > swipeThreshold) {
            handleNext();
        } else if (touchEnd - touchStart > swipeThreshold) {
            handlePrevious();
        }

        setDragOffset(0);
    };

    const handleNext = () => {
        if (currentIndex < phases.length - 1 && !isTransitioning) {
            setIsTransitioning(true);
            setCurrentIndex(prev => prev + 1);
            setTimeout(() => setIsTransitioning(false), 300);
        }
    };

    const handlePrevious = () => {
        if (currentIndex > 0 && !isTransitioning) {
            setIsTransitioning(true);
            setCurrentIndex(prev => prev - 1);
            setTimeout(() => setIsTransitioning(false), 300);
        }
    };

    const handleComplete = () => {
        if (onComplete) {
            onComplete(phases);
        }
    };

    if (!videoId) {
        return (
            <div className="keyframe-swiper-container">
                <div className="error-state">
                    <p>No video uploaded. Please go back and upload a video.</p>
                </div>
            </div>
        );
    }

    if (loading) {
        return (
            <div className="keyframe-swiper-container">
                <div className="loading-state">
                    <div className="spinner"></div>
                    <p>Loading surgical phases...</p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="keyframe-swiper-container">
                <div className="error-state">
                    <p>Error: {error}</p>
                    <button onClick={fetchVLMResults}>Retry</button>
                </div>
            </div>
        );
    }

    if (phases.length === 0) {
        return (
            <div className="keyframe-swiper-container">
                <p>No surgical phases detected</p>
            </div>
        );
    }

    const currentPhase = phases[currentIndex];
    const translateX = isDragging ? dragOffset : 0;

    return (
        <div className="keyframe-swiper-container">
            <div className="swiper-header">
                <h2>Surgical Phase Analysis</h2>
                <div className="phase-counter">
                    Phase {currentIndex + 1} of {phases.length}
                </div>
            </div>

            <div
                ref={containerRef}
                className="swiper-content"
                onTouchStart={handleTouchStart}
                onTouchMove={handleTouchMove}
                onTouchEnd={handleTouchEnd}
                onMouseDown={handleMouseDown}
                onMouseMove={handleMouseMove}
                onMouseUp={handleMouseUp}
                onMouseLeave={handleMouseUp}
            >
                <div
                    className={`swiper-track ${isTransitioning ? 'transitioning' : ''}`}
                    style={{
                        transform: `translateX(calc(-${currentIndex * 100}% + ${translateX}px))`
                    }}
                >
                    {phases.map((phase, index) => (
                        <div key={index} className="swiper-slide">
                            <div className="keyframe-card">
                                {phase.image_base64 && (
                                    <div className="keyframe-image-container">
                                        <img
                                            src={`data:image/jpeg;base64,${phase.image_base64}`}
                                            alt={`Phase ${index + 1}`}
                                            className="keyframe-image"
                                            draggable="false"
                                        />
                                        <div className="timestamp-badge">
                                            {phase.key_timestamp || phase.timestamp || 'N/A'}
                                        </div>
                                    </div>
                                )}

                                <div className="phase-description">
                                    <h3>Phase {index + 1}: {phase.phase_name || 'Surgical Step'}</h3>
                                    <p>{phase.description || 'No description available'}</p>

                                    {phase.timestamp_range && (
                                        <div className="timestamp-range">
                                            Duration: {phase.timestamp_range}
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            <div className="swiper-controls">
                <button
                    className="control-btn prev-btn"
                    onClick={handlePrevious}
                    disabled={currentIndex === 0}
                >
                    ← Previous
                </button>

                <div className="progress-dots">
                    {phases.map((_, index) => (
                        <span
                            key={index}
                            className={`dot ${index === currentIndex ? 'active' : ''}`}
                            onClick={() => {
                                if (!isTransitioning) {
                                    setIsTransitioning(true);
                                    setCurrentIndex(index);
                                    setTimeout(() => setIsTransitioning(false), 300);
                                }
                            }}
                        />
                    ))}
                </div>

                <button
                    className="control-btn next-btn"
                    onClick={handleNext}
                    disabled={currentIndex === phases.length - 1}
                >
                    Next →
                </button>
            </div>

            {currentIndex === phases.length - 1 && (
                <div className="complete-section">
                    <button className="complete-btn" onClick={handleComplete}>
                        Continue to Feedback
                    </button>
                </div>
            )}
        </div>
    );
};

export default KeyframeSwiper;
