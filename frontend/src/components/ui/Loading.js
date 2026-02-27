// src/components/ui/Loading.js
import React from 'react';
import './Loading.css';

function Loading({ text = 'Loading...', size = 'medium' }) {
  return (
    <div className={`loading-container ${size}`}>
      <div className="loading-spinner"></div>
      <p className="loading-text">{text}</p>
    </div>
  );
}

export default Loading;
