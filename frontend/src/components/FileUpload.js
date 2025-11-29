import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import './FileUpload.css';

const FileUpload = ({ onFilesSelect }) => {
    const [sopFile, setSopFile] = useState(null);
    const [videoFile, setVideoFile] = useState(null);

    const onDropSop = useCallback((acceptedFiles) => {
        setSopFile(acceptedFiles[0]);
    }, []);

    const onDropVideo = useCallback((acceptedFiles) => {
        setVideoFile(acceptedFiles[0]);
    }, []);

    const { getRootProps: getSopRootProps, getInputProps: getSopInputProps, isDragActive: isSopDragActive } = useDropzone({
        onDrop: onDropSop,
        accept: 'application/pdf, .doc, .docx',
    });

    const { getRootProps: getVideoRootProps, getInputProps: getVideoInputProps, isDragActive: isVideoDragActive } = useDropzone({
        onDrop: onDropVideo,
        accept: 'video/*',
    });

    const handleNext = () => {
        if (sopFile && videoFile) {
            onFilesSelect(sopFile, videoFile);
        }
    };

    return (
        <div className="file-upload-container">
            <h2>2. Upload SOP and Video Files</h2>
            <div className="drop-zones-container">
                <div {...getSopRootProps()} className={`drop-zone ${isSopDragActive ? 'drag-over' : ''}`}>
                    <input {...getSopInputProps()} />
                    <p>Drag and drop SOP file here, or click to select</p>
                    {sopFile && <div className="file-item"><span>{sopFile.name}</span></div>}
                </div>
                <div {...getVideoRootProps()} className={`drop-zone ${isVideoDragActive ? 'drag-over' : ''}`}>
                    <input {...getVideoInputProps()} />
                    <p>Drag and drop video file here, or click to select</p>
                    {videoFile && <div className="file-item"><span>{videoFile.name}</span></div>}
                </div>
            </div>
            <button className="next-button" onClick={handleNext} disabled={!sopFile || !videoFile}>
                Next
            </button>
        </div>
    );
};

export default FileUpload;
