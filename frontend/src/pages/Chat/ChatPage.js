// src/pages/Chat/ChatPage.js
import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Button, Card, ChatBubble, Loading } from '../../components/ui';
import { useApp } from '../../context/AppContext';
import { speakText, startSpeechRecognition, SPEECH_LANGUAGES, stopSpeaking } from '../../utils/voice';
import './ChatPage.css';

const API_BASE = "http://127.0.0.1:8000";

function ChatPage() {
  const navigate = useNavigate();
  const {
    state,
    setQuestions,
    setAnswers,
    setAnnotatedFields,
    setError,
    setStep,
    reset
  } = useApp();

  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [chatHistory, setChatHistory] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isLoadingQuestions, setIsLoadingQuestions] = useState(true);
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const chatEndRef = useRef(null);

  // Get speech language code
  const getSpeechLanguage = () => {
    const langMap = { 'English': 'en', 'Hindi': 'hi', 'Marathi': 'mr' };
    const langCode = langMap[state.selectedLanguage] || 'en';
    return SPEECH_LANGUAGES[langCode] || 'en-US';
  };

  // Generate questions on mount
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => {
    const generateQuestions = async () => {
      try {
        setIsLoadingQuestions(true);
        const response = await axios.post(`${API_BASE}/generate_questions`, {
          form_id: state.formId,
          language: state.selectedLanguage,
          fields: state.fields,
        });

        const questions = response.data.questions;
        setQuestions(questions);

        // Add welcome message to chat
        const welcomeMessage = getWelcomeMessage(state.selectedLanguage);
        setChatHistory([
          {
            type: 'bot',
            message: welcomeMessage,
            fieldName: null
          },
          {
            type: 'bot',
            message: questions[0]?.question_text || 'What is your name?',
            fieldName: questions[0]?.field_name || 'Name'
          }
        ]);
      } catch (err) {
        console.error('Error generating questions:', err);
        setError('Failed to generate questions. Please try again.');
      } finally {
        setIsLoadingQuestions(false);
      }
    };

    if (state.formId && state.fields.length > 0) {
      generateQuestions();
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [state.formId, state.fields, state.selectedLanguage]);

  // Scroll to bottom of chat
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatHistory]);

  // Speak the current question when it changes
  useEffect(() => {
    if (chatHistory.length > 1 && state.questions[currentQuestionIndex]) {
      const currentQuestion = state.questions[currentQuestionIndex];
      // Auto-speak the question (optional - can be disabled)
      // speakQuestion(currentQuestion.question_text);
    }
  }, [currentQuestionIndex]);

  const speakQuestion = async (text) => {
    try {
      setIsSpeaking(true);
      await speakText(text, getSpeechLanguage());
    } catch (err) {
      console.log('Speech not available:', err);
    } finally {
      setIsSpeaking(false);
    }
  };

  const handleVoiceInput = async () => {
    try {
      setIsListening(true);
      const transcript = await startSpeechRecognition(getSpeechLanguage());
      setInputValue(transcript);
    } catch (err) {
      console.error('Voice input error:', err);
      setError('Voice input failed. Please type your answer.');
    } finally {
      setIsListening(false);
    }
  };

  const handleSpeakQuestion = () => {
    const currentQuestion = state.questions[currentQuestionIndex];
    if (currentQuestion) {
      speakQuestion(currentQuestion.question_text);
    }
  };

  const getWelcomeMessage = (language) => {
    if (language === 'Hindi') {
      return 'नमस्ते! मैं आपकी फॉर्म भरने में मदद करूंगा। आप वॉइस से जवाब दे सकते हैं या टाइप कर सकते हैं।';
    } else if (language === 'Marathi') {
      return 'नमस्कार! मी तुमची फॉर्म भरण्यास मदत करेन. तुम्ही वॉइसने उत्तर देऊ शकता किंवा टाइप करू शकता.';
    }
    return 'Hello! I will help you fill out this form. You can answer using voice or type.';
  };

  const handleSendAnswer = () => {
    if (!inputValue.trim()) return;

    const currentQuestion = state.questions[currentQuestionIndex];
    const newAnswer = { [currentQuestion.id]: inputValue };
    
    // Add user answer to chat
    setChatHistory(prev => [
      ...prev,
      {
        type: 'user',
        message: inputValue,
        fieldName: currentQuestion.field_name
      }
    ]);

    // Save answer
    setAnswers(newAnswer);
    setInputValue('');

    // Move to next question or submit
    if (currentQuestionIndex < state.questions.length - 1) {
      setTimeout(() => {
        const nextIndex = currentQuestionIndex + 1;
        setCurrentQuestionIndex(nextIndex);
        setChatHistory(prev => [
          ...prev,
          {
            type: 'bot',
            message: state.questions[nextIndex].question_text,
            fieldName: state.questions[nextIndex].field_name
          }
        ]);
        // Speak the next question automatically
        speakQuestion(state.questions[nextIndex].question_text);
      }, 500);
    } else {
      handleSubmitAllAnswers();
    }
  };

  const handleSubmitAllAnswers = async () => {
    setIsSubmitting(true);
    try {
      const response = await axios.post(`${API_BASE}/submit_answers`, {
        form_id: state.formId,
        answers: state.answers,
      });

      setAnnotatedFields(response.data.annotated_fields);
      setStep('preview');
      navigate('/preview');
    } catch (err) {
      console.error('Error submitting answers:', err);
      setError('Failed to submit answers. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendAnswer();
    }
  };

  const handleStartOver = () => {
    stopSpeaking();
    reset();
    navigate('/');
  };

  if (isLoadingQuestions) {
    return (
      <div className="chat-page">
        <Loading text="Preparing your questions..." size="large" />
      </div>
    );
  }

  return (
    <div className="chat-page">
      <div className="chat-container">
        <Card className="chat-card" padding="medium">
          <div className="chat-header">
            <div className="header-info">
              <span className="language-badge">{state.selectedLanguage}</span>
              <span className="progress-text">
                Question {currentQuestionIndex + 1} of {state.questions.length}
              </span>
            </div>
            <button className="start-over-btn" onClick={handleStartOver}>
              Start Over
            </button>
          </div>

          <div className="progress-bar">
            <div 
              className="progress-fill"
              style={{ width: `${((currentQuestionIndex + 1) / state.questions.length) * 100}%` }}
            />
          </div>

          <div className="chat-messages">
            {chatHistory.map((chat, index) => (
              <ChatBubble
                key={index}
                message={chat.message}
                isUser={chat.type === 'user'}
                showFieldName={chat.type === 'user'}
                fieldName={chat.fieldName}
              />
            ))}
            <div ref={chatEndRef} />
          </div>

          {isSubmitting ? (
            <div className="submitting-section">
              <Loading text="Submitting your answers..." />
            </div>
          ) : (
            <div className="chat-input-section">
              <div className="current-field">
                <span className="field-label">Current Field:</span>
                <span className="field-name">
                  {state.questions[currentQuestionIndex]?.field_name || ''}
                </span>
              </div>
              <div className="input-row">
                <button 
                  className={`voice-btn listen-btn ${isListening ? 'listening' : ''}`}
                  onClick={handleVoiceInput}
                  disabled={isListening}
                  title="Click to speak your answer"
                >
                  {isListening ? '🎤...' : '🎤'}
                </button>
                <input
                  type="text"
                  className="chat-input"
                  placeholder={`Type or speak your answer in ${state.selectedLanguage}...`}
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyPress={handleKeyPress}
                />
                <button 
                  className={`voice-btn speak-btn ${isSpeaking ? 'speaking' : ''}`}
                  onClick={handleSpeakQuestion}
                  disabled={isSpeaking}
                  title="Click to hear the question"
                >
                  🔊
                </button>
                <Button 
                  variant="primary"
                  onClick={handleSendAnswer}
                  disabled={!inputValue.trim()}
                >
                  Send
                </Button>
              </div>
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}

export default ChatPage;
