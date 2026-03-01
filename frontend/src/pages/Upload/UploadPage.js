// src/pages/Upload/UploadPage.js
import React from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Button, Card, FileUpload, Loading } from '../../components/ui';
import { useApp } from '../../context/AppContext';
import './UploadPage.css';

const API_BASE = "http://127.0.0.1:8000";

function UploadPage() {
  const navigate = useNavigate();
  const { 
    state, 
    setFile, 
    setFormId, 
    setFields, 
    setUploading, 
    setError,
    setStep 
  } = useApp();

  const handleFileSelect = (file) => {
    // Create preview URL
    const preview = URL.createObjectURL(file);
    setFile(file, preview);
  };

  const handleUpload = async () => {
    if (!state.file) {
      setError('Please select a file first');
      return;
    }

    setUploading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('file', state.file);

      const response = await axios.post(`${API_BASE}/upload_form`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        params: { language: state.selectedLanguage }
      });

      setFormId(response.data.form_id);
      setFields(response.data.fields);
      setStep('explain');
      navigate('/explain');
    } catch (err) {
      console.error('Upload error:', err);
      setError(err.response?.data?.detail || 'Failed to upload form. Please try again.');
    } finally {
      setUploading(false);
    }
  };

  const handleBack = () => {
    navigate('/language');
  };

  const handleRemoveFile = () => {
    if (state.filePreview) {
      URL.revokeObjectURL(state.filePreview);
    }
    setFile(null, null);
  };

  return (
    <div className="upload-page">
      <div className="upload-container">
        <Card className="upload-card" padding="large">
          <div className="page-header">
            <button className="back-button" onClick={handleBack}>
              ← Back
            </button>
            <div className="step-indicator">
              <span className="step completed">1</span>
              <span className="step-line"></span>
              <span className="step completed">2</span>
              <span className="step-line"></span>
              <span className="step active">3</span>
              <span className="step-line"></span>
              <span className="step">4</span>
            </div>
          </div>

          <div className="upload-content">
            <h1>Upload Your Form</h1>
            <h2>अपना फॉर्म अपलोड करें</h2>
            <p className="upload-description">
              Take a clear photo or scan of your form. Make sure all text is readable.
            </p>

            {state.isUploading ? (
              <Loading text="Processing your form... This may take a moment." />
            ) : state.filePreview ? (
              <div className="file-preview-container">
                <img 
                  src={state.filePreview} 
                  alt="Form preview" 
                  className="file-preview"
                />
                <button 
                  className="remove-file-btn"
                  onClick={handleRemoveFile}
                >
                  × Remove
                </button>
              </div>
            ) : (
              <FileUpload
                onFileSelect={handleFileSelect}
                accept="image/*,.pdf"
              />
            )}

            {state.error && (
              <div className="error-message">
                {state.error}
              </div>
            )}

            <div className="upload-actions">
              <Button 
                variant="primary" 
                size="large"
                onClick={handleUpload}
                disabled={!state.file || state.isUploading}
                icon="→"
              >
                {state.isUploading ? 'Processing...' : 'Continue / जारी रखें'}
              </Button>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}

export default UploadPage;
