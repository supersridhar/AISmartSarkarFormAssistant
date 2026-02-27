// src/components/ui/ChatBubble.js
import React from 'react';
import './ChatBubble.css';

function ChatBubble({ 
  message, 
  isUser = false, 
  timestamp,
  showFieldName = false,
  fieldName 
}) {
  return (
    <div className={`chat-bubble ${isUser ? 'user' : 'bot'}`}>
      <div className="bubble-content">
        {showFieldName && fieldName && (
          <span className="field-label">{fieldName}</span>
        )}
        <p className="message-text">{message}</p>
        {timestamp && (
          <span className="message-timestamp">{timestamp}</span>
        )}
      </div>
    </div>
  );
}

export default ChatBubble;
