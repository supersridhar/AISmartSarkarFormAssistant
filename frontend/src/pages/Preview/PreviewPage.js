// src/pages/Preview/PreviewPage.js
import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Button, Card } from '../../components/ui';
import { useApp } from '../../context/AppContext';
import './PreviewPage.css';

function PreviewPage() {
  const navigate = useNavigate();
  const { state, reset } = useApp();

  const handleStartOver = () => {
    reset();
    navigate('/');
  };

  const handleDownload = () => {
    // In a real implementation, this would generate a PDF or annotated image
    // For now, we'll just show the data
    alert('Download functionality would generate a filled form here!');
  };

  return (
    <div className="preview-page">
      <div className="preview-container">
        <Card className="preview-card" padding="large">
          <div className="success-header">
            <div className="success-icon">✓</div>
            <h1>Form Completed!</h1>
            <h2>फॉर्म पूरा हुआ!</h2>
          </div>

          <div className="preview-content">
            <div className="form-preview-section">
              <h3>Your Form Preview</h3>
              {state.filePreview && (
                <div className="image-preview-container">
                  <img 
                    src={state.filePreview} 
                    alt="Original form" 
                    className="form-image"
                  />
                  {/* Overlay annotations */}
                  {state.annotatedFields.map((field, index) => (
                    <div
                      key={index}
                      className="annotation-overlay"
                      style={{
                        left: `${field.x}px`,
                        top: `${field.y}px`,
                      }}
                      title={`${field.field_name}: ${field.value}`}
                    >
                      {field.value}
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="answers-summary">
              <h3>Filled Information</h3>
              <div className="answers-list">
                {state.annotatedFields.map((field, index) => (
                  <div key={index} className="answer-item">
                    <span className="answer-label">{field.field_name}</span>
                    <span className="answer-value">{field.value}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="preview-actions">
            <Button 
              variant="secondary" 
              size="large"
              onClick={handleStartOver}
            >
              Start New Form / नया फॉर्म
            </Button>
            <Button 
              variant="success" 
              size="large"
              onClick={handleDownload}
              icon="↓"
            >
              Download Filled Form / फॉर्म डाउनलोड करें
            </Button>
          </div>
        </Card>
      </div>
    </div>
  );
}

export default PreviewPage;
