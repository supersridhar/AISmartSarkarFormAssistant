// src/App.js
import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AppProvider } from './context/AppContext';
import { 
  HomePage, 
  LanguageSelectionPage, 
  UploadPage, 
  ChatPage, 
  PreviewPage 
} from './pages';
import './App.css';

function App() {
  return (
    <AppProvider>
      <Router>
        <div className="app">
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/language" element={<LanguageSelectionPage />} />
            <Route path="/upload" element={<UploadPage />} />
            <Route path="/chat" element={<ChatPage />} />
            <Route path="/preview" element={<PreviewPage />} />
          </Routes>
        </div>
      </Router>
    </AppProvider>
  );
}

export default App;
