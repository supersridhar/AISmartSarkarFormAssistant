// src/components/ui/Card.js
import React from 'react';
import './Card.css';

function Card({ 
  children, 
  title, 
  subtitle,
  className = '',
  padding = 'medium',
  hoverable = false,
  onClick
}) {
  return (
    <div 
      className={`ui-card ${padding} ${hoverable ? 'hoverable' : ''} ${className}`}
      onClick={onClick}
    >
      {(title || subtitle) && (
        <div className="card-header">
          {title && <h3 className="card-title">{title}</h3>}
          {subtitle && <p className="card-subtitle">{subtitle}</p>}
        </div>
      )}
      <div className="card-content">
        {children}
      </div>
    </div>
  );
}

export default Card;
