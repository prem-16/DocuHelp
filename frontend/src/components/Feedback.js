import React, { useState } from 'react';
import './Feedback.css';

const mockData = [
    {
        image: 'https://via.placeholder.com/600x400?text=Step+1',
        description: 'Initial incision is made.'
    },
    {
        image: 'https://via.placeholder.com/600x400?text=Step+2',
        description: 'The surgeon uses forceps to grasp the tissue.'
    },
    {
        image: 'https://via.placeholder.com/600x400?text=Step+3',
        description: 'The area is sutured.'
    }
];

const Feedback = ({ onFeedbackComplete }) => {
    const [currentIndex, setCurrentIndex] = useState(0);
    const [report, setReport] = useState([]);

    const handleFeedback = (isCorrect) => {
        if (isCorrect) {
            setReport([...report, mockData[currentIndex]]);
        }

        if (currentIndex < mockData.length - 1) {
            setCurrentIndex(currentIndex + 1);
        } else {
            onFeedbackComplete(report);
        }
    };

    if (currentIndex >= mockData.length) {
        return <div>Thank you for your feedback!</div>;
    }

    return (
        <div className="feedback-container">
            <h2>4. Review Analysis</h2>
            <div className="feedback-card">
                <img src={mockData[currentIndex].image} alt="Surgery step" />
                <p>{mockData[currentIndex].description}</p>
            </div>
            <div className="feedback-buttons">
                <button className="incorrect" onClick={() => handleFeedback(false)}>Incorrect</button>
                <button className="correct" onClick={() => handleFeedback(true)}>Correct</button>
            </div>
        </div>
    );
};

export default Feedback;
