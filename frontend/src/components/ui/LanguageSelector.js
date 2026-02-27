// src/components/ui/LanguageSelector.js
import React from 'react';
import './LanguageSelector.css';

const LANGUAGES = [
  { code: 'Hindi', name: 'हिंदी', native: 'Hindi', flag: '🇮🇳' },
  { code: 'Marathi', name: 'मराठी', native: 'Marathi', flag: '🇮🇳' },
];

function LanguageSelector({ selectedLanguage, onSelect, disabled = false }) {
  return (
    <div className={`language-selector ${disabled ? 'disabled' : ''}`}>
      {LANGUAGES.map((lang) => (
        <button
          key={lang.code}
          className={`language-option ${selectedLanguage === lang.code ? 'selected' : ''}`}
          onClick={() => !disabled && onSelect(lang.code)}
          disabled={disabled}
        >
          <span className="lang-flag">{lang.flag}</span>
          <div className="lang-info">
            <span className="lang-name">{lang.name}</span>
            <span className="lang-native">{lang.native}</span>
          </div>
          {selectedLanguage === lang.code && (
            <span className="check-icon">✓</span>
          )}
        </button>
      ))}
    </div>
  );
}

export default LanguageSelector;
