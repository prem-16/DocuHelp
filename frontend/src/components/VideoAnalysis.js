import React from 'react';
import KeyframeSwiper from './KeyframeSwiper';
import './VideoAnalysis.css';

const VideoAnalysis = ({ videoId, onAnalysisComplete }) => {
    const handleComplete = (phases) => {
        console.log('Analysis complete with phases:', phases);
        if (onAnalysisComplete) {
            onAnalysisComplete(phases);
        }
    };

    return (
        <div className="video-analysis-container">
            <KeyframeSwiper
                videoId={videoId}
                onComplete={handleComplete}
            />
        </div>
    );
};

export default VideoAnalysis;
