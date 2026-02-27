// src/components/ui/Button.js
import React from 'react';
import './Button.css';

function Button({ 
  children, 
  onClick, 
  variant = 'primary', 
  size = 'medium',
  disabled = false,
  type = 'button',
  className = '',
  icon
}) {
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={`ui-button ${variant} ${size} ${className} ${disabled ? 'disabled' : ''}`}
    >
      {icon && <span className="button-icon">{icon}</span>}
      {children}
    </button>
  );
}

export default Button;
