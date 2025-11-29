import React from 'react';
import './Report.css';

const Report = ({ reportData }) => {
    return (
        <div className="report-container">
            <h2>7. Report Overview</h2>
            <div className="report-overview">
                {reportData.map((item, index) => (
                    <div className="report-item" key={index}>
                        <img src={item.image} alt={`Step ${index + 1}`} />
                        <p>{item.description}</p>
                    </div>
                ))}
            </div>
            <button className="next-button">Generate Report</button>
        </div>
    );
};

export default Report;
