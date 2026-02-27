// src/pages/Language/LanguageSelectionPage.js
import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Button, Card, LanguageSelector } from '../../components/ui';
import { useApp } from '../../context/AppContext';
import './LanguageSelectionPage.css';

function LanguageSelectionPage() {
  const navigate = useNavigate();
  const { state, setLanguage, setStep } = useApp();

  const handleLanguageSelect = (language) => {
    setLanguage(language);
  };

  const handleContinue = () => {
    if (state.selectedLanguage) {
      setStep('upload');
      navigate('/upload');
    }
  };

  const handleBack = () => {
    navigate('/');
  };

  return (
    <div className="language-page">
      <div className="language-container">
        <Card className="language-card" padding="large">
          <div className="page-header">
            <button className="back-button" onClick={handleBack}>
              ← Back
            </button>
            <div className="step-indicator">
              <span className="step completed">1</span>
              <span className="step-line"></span>
              <span className="step active">2</span>
              <span className="step-line"></span>
              <span className="step">3</span>
              <span className="step-line"></span>
              <span className="step">4</span>
            </div>
          </div>

          <div className="language-content">
            <h1>Select Your Language</h1>
            <h2>आपकी भाषा चुनें</h2>
            <p className="language-description">
              Questions will be asked in your selected language. 
              You can answer in {state.selectedLanguage || 'Hindi'} or English.
            </p>

            <LanguageSelector
              selectedLanguage={state.selectedLanguage}
              onSelect={handleLanguageSelect}
            />

            <div className="language-actions">
              <Button 
                variant="primary" 
                size="large"
                onClick={handleContinue}
                disabled={!state.selectedLanguage}
                icon="→"
              >
                Continue / जारी रखें
              </Button>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}

export default LanguageSelectionPage;
