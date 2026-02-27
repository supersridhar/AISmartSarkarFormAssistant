// src/pages/Chat/ChatPage.js
import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Button, Card, ChatBubble, Loading } from '../../components/ui';
import { useApp } from '../../context/AppContext';
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
  const chatEndRef = useRef(null);

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

  const getWelcomeMessage = (language) => {
    if (language === 'Hindi') {
      return 'नमस्ते! मैं आपकी फॉर्म भरने में मदद करूंगा। कृपया नीचे दिए गए सवालों का जवाब दें।';
    } else if (language === 'Marathi') {
      return 'नमस्कार! मी तुमची फॉर्म भरण्यास मदत करेन. कृपया खाली दिलेल्या प्रश्नांची उत्तरे द्या.';
    }
    return 'Hello! I will help you fill out this form. Please answer the questions below.';
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
                <input
                  type="text"
                  className="chat-input"
                  placeholder={`Type your answer in ${state.selectedLanguage} or English...`}
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyPress={handleKeyPress}
                />
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
