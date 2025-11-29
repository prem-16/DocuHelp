import React, { useState } from 'react';
import './ProcedureSelection.css';

const procedures = [
    'Laparoscopic Cholecystectomy',
    'Appendectomy',
    'Hernia Repair',
    'Coronary Artery Bypass Grafting',
    'Knee Arthroscopy',
    'Total Hip Replacement'
];

const ProcedureSelection = ({ onProcedureSelect }) => {
    const [selected, setSelected] = useState(null);

    const handleSelect = (procedure) => {
        setSelected(procedure);
        onProcedureSelect(procedure);
    };

    return (
        <div className="procedure-selection-container">
            <h2>1. Select a Surgical Procedure</h2>
            <div className="procedure-list">
                {procedures.map((procedure, index) => (
                    <button
                        key={index}
                        className={`procedure-button ${selected === procedure ? 'selected' : ''}`}
                        onClick={() => handleSelect(procedure)}
                    >
                        {procedure}
                    </button>
                ))}
            </div>
        </div>
    );
};

export default ProcedureSelection;
