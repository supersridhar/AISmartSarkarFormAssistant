// src/context/AppContext.js
import React, { createContext, useContext, useReducer } from 'react';

// Initial state
const initialState = {
  // Form data
  formId: null,
  file: null,
  filePreview: null,
  
  // Language selection
  selectedLanguage: 'Hindi', // Hindi or Marathi
  
  // Extracted fields from OCR
  fields: [],
  
  // Form explanation from LLM
  formExplanation: null,
  
  // Questions for chat
  questions: [],
  
  // User answers
  answers: {},
  
  // Annotated form data
  annotatedFields: [],
  
  // Loading states
  isUploading: false,
  isProcessing: false,
  isGeneratingQuestions: false,
  isSubmitting: false,
  
  // Error state
  error: null,
  
  // Current step in the flow
  currentStep: 'home', // home -> language -> upload -> chat -> preview
};

// Action types
const ActionTypes = {
  SET_FILE: 'SET_FILE',
  SET_FORM_ID: 'SET_FORM_ID',
  SET_LANGUAGE: 'SET_LANGUAGE',
  SET_FIELDS: 'SET_FIELDS',
  SET_FORM_EXPLANATION: 'SET_FORM_EXPLANATION',
  SET_QUESTIONS: 'SET_QUESTIONS',
  SET_ANSWERS: 'SET_ANSWERS',
  SET_ANNOTATED_FIELDS: 'SET_ANNOTATED_FIELDS',
  SET_LOADING: 'SET_LOADING',
  SET_PROCESSING: 'SET_PROCESSING',
  SET_ERROR: 'SET_ERROR',
  SET_STEP: 'SET_STEP',
  RESET: 'RESET',
};

// Reducer function
function appReducer(state, action) {
  switch (action.type) {
    case ActionTypes.SET_FILE:
      return { ...state, file: action.payload.file, filePreview: action.payload.preview };
    case ActionTypes.SET_FORM_ID:
      return { ...state, formId: action.payload };
    case ActionTypes.SET_LANGUAGE:
      return { ...state, selectedLanguage: action.payload };
    case ActionTypes.SET_FIELDS:
      return { ...state, fields: action.payload };
    case ActionTypes.SET_FORM_EXPLANATION:
      return { ...state, formExplanation: action.payload };
    case ActionTypes.SET_QUESTIONS:
      return { ...state, questions: action.payload };
    case ActionTypes.SET_ANSWERS:
      return { ...state, answers: { ...state.answers, ...action.payload } };
    case ActionTypes.SET_ANNOTATED_FIELDS:
      return { ...state, annotatedFields: action.payload };
    case ActionTypes.SET_LOADING:
      return { ...state, isUploading: action.payload };
    case ActionTypes.SET_PROCESSING:
      return { ...state, isProcessing: action.payload };
    case ActionTypes.SET_ERROR:
      return { ...state, error: action.payload };
    case ActionTypes.SET_STEP:
      return { ...state, currentStep: action.payload };
    case ActionTypes.RESET:
      return { ...initialState };
    default:
      return state;
  }
}

// Create context
const AppContext = createContext();

// Provider component
export function AppProvider({ children }) {
  const [state, dispatch] = useReducer(appReducer, initialState);

  // Action creators
  const actions = {
    setFile: (file, preview) => dispatch({ 
      type: ActionTypes.SET_FILE, 
      payload: { file, preview } 
    }),
    setFormId: (formId) => dispatch({ type: ActionTypes.SET_FORM_ID, payload: formId }),
    setLanguage: (language) => dispatch({ type: ActionTypes.SET_LANGUAGE, payload: language }),
    setFields: (fields) => dispatch({ type: ActionTypes.SET_FIELDS, payload: fields }),
    setFormExplanation: (explanation) => dispatch({ type: ActionTypes.SET_FORM_EXPLANATION, payload: explanation }),
    setQuestions: (questions) => dispatch({ type: ActionTypes.SET_QUESTIONS, payload: questions }),
    setAnswers: (answers) => dispatch({ type: ActionTypes.SET_ANSWERS, payload: answers }),
    setAnnotatedFields: (fields) => dispatch({ type: ActionTypes.SET_ANNOTATED_FIELDS, payload: fields }),
    setUploading: (isUploading) => dispatch({ type: ActionTypes.SET_LOADING, payload: isUploading }),
    setProcessing: (isProcessing) => dispatch({ type: ActionTypes.SET_PROCESSING, payload: isProcessing }),
    setError: (error) => dispatch({ type: ActionTypes.SET_ERROR, payload: error }),
    setStep: (step) => dispatch({ type: ActionTypes.SET_STEP, payload: step }),
    reset: () => dispatch({ type: ActionTypes.RESET }),
  };

  return (
    <AppContext.Provider value={{ state, ...actions }}>
      {children}
    </AppContext.Provider>
  );
}

// Custom hook to use context
export function useApp() {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
}

export default AppContext;
