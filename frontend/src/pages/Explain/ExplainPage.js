// src/pages/Explain/ExplainPage.js
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Button, Card, Loading } from '../../components/ui';
import { useApp } from '../../context/AppContext';
import { speakText, stopSpeaking, SPEECH_LANGUAGES } from '../../utils/voice';
import './ExplainPage.css';

const API_BASE = "http://127.0.0.1:8000";

function ExplainPage() {
  const navigate = useNavigate();
  const {
    state,
    setFormExplanation,
    setQuestions,
    setError,
    setStep
  } = useApp();

  const [isExplaining, setIsExplaining] = useState(true);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [explanation, setExplanation] = useState(null);

  // Get speech language code
  const getSpeechLanguage = () => {
    const langMap = { 'English': 'en', 'Hindi': 'hi', 'Marathi': 'mr' };
    const langCode = langMap[state.selectedLanguage] || 'hi';
    return SPEECH_LANGUAGES[langCode] || 'hi-IN';
  };

  useEffect(() => {
    const explainForm = async () => {
      try {
        setIsExplaining(true);
        
        // Get language codes
        const langMap = { 'English': 'en', 'Hindi': 'hi', 'Marathi': 'mr' };
        const targetLang = langMap[state.selectedLanguage] || 'hi';
        console.log('Calling multilingual endpoint with:', { form_id: state.formId, targetLang });
        
        // Call the new multilingual endpoint
        const response = await axios.post(`${API_BASE}/explain_form_multilingual`, {
          form_id: state.formId,
          source_language: 'en',  // Assume form is in English (OCR output)
          target_language: targetLang  // Explain in user's selected language
        });

        console.log('API Response:', response.data);
        const exp = response.data;
        
        // Transform to match expected format
        const transformedExp = {
          form_type: exp.form_type,
          purpose: exp.purpose,
          sections: exp.sections?.map(s => s.title) || [],
          summary: exp.explanation_in_target_language,
          form_category: exp.form_category,
          issuing_authority: exp.issuing_authority,
          required_documents: exp.required_documents,
          important_notes: exp.important_notes
        };
        
        console.log('Transformed explanation:', transformedExp);
        setExplanation(transformedExp);
        setFormExplanation(transformedExp);
        
        // NOTE: Removed automatic TTS - only play on button click
        
      } catch (err) {
        console.error('Error explaining form:', err);
        console.error('Error response:', err.response?.data);
        // Fallback - continue without explanation
        setExplanation({
          form_type: 'Form',
          purpose: 'This form collects your information',
          sections: ['Personal Details', 'Contact Information'],
          summary: 'Please answer the questions to fill this form.'
        });
      } finally {
        setIsExplaining(false);
      }
    };

    if (state.formId) {
      explainForm();
    }
  }, [state.formId, state.selectedLanguage]);

  const handleSpeakExplanation = async () => {
    if (!explanation) return;
    
    // If already speaking, stop it
    if (isSpeaking) {
      stopSpeaking();
      setIsSpeaking(false);
      return;
    }
    
    try {
      setIsSpeaking(true);
      const fullExplanation = `${explanation.purpose}. ${explanation.summary}`;
      await speakText(fullExplanation, getSpeechLanguage());
    } catch (err) {
      console.log('Speech error:', err);
    } finally {
      setIsSpeaking(false);
    }
  };

  const handleContinue = () => {
    setStep('chat');
    navigate('/chat');
  };

  const handleBack = () => {
    navigate('/upload');
  };

  if (isExplaining) {
    return (
      <div className="explain-page">
        <Loading text="Analyzing your form..." size="large" />
      </div>
    );
  }

  return (
    <div className="explain-page">
      <div className="explain-container">
        <Card className="explain-card" padding="large">
          <div className="page-header">
            <button className="back-button" onClick={handleBack}>
              ← Back
            </button>
            <div className="step-indicator">
              <span className="step completed">1</span>
              <span className="step-line"></span>
              <span className="step completed">2</span>
              <span className="step-line"></span>
              <span className="step completed">3</span>
              <span className="step-line"></span>
              <span className="step active">4</span>
              <span className="step-line"></span>
              <span className="step">5</span>
            </div>
          </div>

          <div className="explain-content">
            <h1>Form Analysis / फॉर्म विश्लेषण</h1>
            
            {explanation && (
              <div className="explanation-details">
                <div className="explanation-section">
                  <h3>Form Type / फॉर्म का प्रकार</h3>
                  <p className="form-type">{explanation.form_type}</p>
                  {explanation.form_category && (
                    <p className="form-category">Category: {explanation.form_category}</p>
                  )}
                </div>

                <div className="explanation-section">
                  <h3>Purpose / उद्देश्य</h3>
                  <p className="purpose">{explanation.purpose}</p>
                </div>

                {explanation.issuing_authority && (
                  <div className="explanation-section">
                    <h3>Issuing Authority / जारी करने वाला प्राधिकारी</h3>
                    <p>{explanation.issuing_authority}</p>
                  </div>
                )}

                {explanation.sections && explanation.sections.length > 0 && (
                  <div className="explanation-section">
                    <h3>Sections / खंड</h3>
                    <ul className="sections-list">
                      {explanation.sections.map((section, index) => (
                        <li key={index}>{section}</li>
                      ))}
                    </ul>
                  </div>
                )}

                <div className="explanation-section summary-section">
                  <h3>Explanation / सारांश</h3>
                  <p className="summary">{explanation.summary}</p>
                </div>

                {explanation.required_documents && explanation.required_documents.length > 0 && (
                  <div className="explanation-section">
                    <h3>Required Documents / आवश्यक दस्तावेज़</h3>
                    <ul className="sections-list">
                      {explanation.required_documents.map((doc, index) => (
                        <li key={index}>{doc}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {explanation.important_notes && explanation.important_notes.length > 0 && (
                  <div className="explanation-section notes-section">
                    <h3>Important Notes / महत्वपूर्ण नोट्स</h3>
                    <ul className="sections-list">
                      {explanation.important_notes.map((note, index) => (
                        <li key={index}>{note}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}

            <div className="voice-controls">
              <button 
                className={`voice-btn speak-btn ${isSpeaking ? 'speaking' : ''}`}
                onClick={handleSpeakExplanation}
                title={isSpeaking ? "Stop" : "Listen to explanation"}
              >
                {isSpeaking ? '⏹ Stop' : '🔊 Listen'}
              </button>
            </div>

            <div className="explain-actions">
              <Button 
                variant="primary" 
                size="large"
                onClick={handleContinue}
                icon="→"
              >
                Continue to Fill Form / फॉर्म भरना शुरू करें
              </Button>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}

export default ExplainPage;
