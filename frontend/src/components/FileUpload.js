import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import './FileUpload.css';

const FileUpload = ({ onFilesSelect, selectedProcedure }) => {
    const [videoFile, setVideoFile] = useState(null);
    const [isUploading, setIsUploading] = useState(false);
    const [uploadError, setUploadError] = useState(null);

    const onDropVideo = useCallback((acceptedFiles, rejectedFiles) => {
        setUploadError(null);

        if (rejectedFiles && rejectedFiles.length > 0) {
            setUploadError(rejectedFiles[0].errors[0].message);
            return;
        }

        if (acceptedFiles && acceptedFiles.length > 0) {
            setVideoFile(acceptedFiles[0]);
        }
    }, []);

    const { getRootProps: getVideoRootProps, getInputProps: getVideoInputProps, isDragActive: isVideoDragActive } = useDropzone({
        onDrop: onDropVideo,
        accept: {
            'video/mp4': ['.mp4'],
            'video/avi': ['.avi'],
            'video/quicktime': ['.mov'],
            'video/x-msvideo': ['.avi']
        },
        maxFiles: 1,
        validator: (file) => {
            const validTypes = ['video/mp4', 'video/avi', 'video/mov', 'video/quicktime', 'video/x-msvideo'];
            if (!validTypes.includes(file.type)) {
                return {
                    code: 'invalid-file-type',
                    message: `Invalid file type: ${file.type}. Please upload MP4, AVI, or MOV files only.`
                };
            }
            // 500MB max file size
            const maxSize = 500 * 1024 * 1024;
            if (file.size > maxSize) {
                return {
                    code: 'file-too-large',
                    message: `File is too large. Maximum size is 500MB.`
                };
            }
            return null;
        }
    });

    const handleNext = async () => {
        if (videoFile) {
            setIsUploading(true);
            setUploadError(null);
            try {
                await onFilesSelect(null, videoFile);
            } catch (error) {
                console.error('Upload error:', error);
                setUploadError(error.message || 'Upload failed. Please try again.');
            } finally {
                setIsUploading(false);
            }
        }
    };

    const formatFileSize = (bytes) => {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
    };

    return (
        <div className="file-upload-container">
            <h2>2. Upload Surgical Video</h2>
            {selectedProcedure && (
                <div className="selected-procedure-banner">
                    <span className="procedure-icon">🏥</span>
                    <div>
                        <strong>Selected Procedure:</strong>
                        <div className="procedure-name">{selectedProcedure}</div>
                    </div>
                </div>
            )}

            <div className="upload-instruction">
                <p>Upload your surgical video for AI-powered analysis and documentation</p>
            </div>

            <div className="drop-zone-wrapper">
                <div {...getVideoRootProps()} className={`drop-zone-large ${isVideoDragActive ? 'drag-over' : ''} ${videoFile ? 'has-file' : ''}`}>
                    <input {...getVideoInputProps()} />
                    {!videoFile ? (
                        <>
                            <div className="upload-icon">📹</div>
                            <p className="upload-title">
                                {isVideoDragActive ? 'Drop video here' : 'Drag & drop your video here'}
                            </p>
                            <p className="upload-subtitle">or click to browse</p>
                            <div className="upload-formats">
                                <span className="format-badge">MP4</span>
                                <span className="format-badge">AVI</span>
                                <span className="format-badge">MOV</span>
                            </div>
                            <small className="upload-note">Maximum file size: 500MB</small>
                        </>
                    ) : (
                        <div className="file-preview">
                            <div className="file-icon">✓</div>
                            <div className="file-details">
                                <strong className="file-name">{videoFile.name}</strong>
                                <p className="file-size">{formatFileSize(videoFile.size)}</p>
                            </div>
                            <button
                                className="remove-file-btn"
                                onClick={(e) => {
                                    e.stopPropagation();
                                    setVideoFile(null);
                                    setUploadError(null);
                                }}
                            >
                                ✕
                            </button>
                        </div>
                    )}
                </div>
            </div>

            {uploadError && (
                <div className="upload-error">
                    <span className="error-icon">⚠️</span>
                    {uploadError}
                </div>
            )}

            <button
                className="next-button"
                onClick={handleNext}
                disabled={!videoFile || isUploading}
            >
                {isUploading ? (
                    <>
                        <span className="button-spinner"></span>
                        Uploading & Processing...
                    </>
                ) : (
                    'Upload & Start Analysis'
                )}
            </button>
        </div>
    );
};

export default FileUpload;
