// src/pages/Home/HomePage.js
import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Button, Card } from '../../components/ui';
import './HomePage.css';

function HomePage() {
  const navigate = useNavigate();

  const handleStartFilling = () => {
    navigate('/language');
  };

  return (
    <div className="home-page">
      <div className="home-container">
        <div className="hero-section">
          <div className="logo-section">
            <div className="logo-icon">
              <svg width="80" height="80" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                <polyline points="14 2 14 8" />
               8 20  <line x1="16" y1="13" x2="8" y2="13" />
                <line x1="16" y1="17" x2="8" y2="17" />
                <polyline points="10 9 9 9 8 9" />
              </svg>
            </div>
            <h1 className="app-title">Form Seva</h1>
            <p className="app-tagline">आपके फॉर्म, आपकी भाषा में</p>
          </div>

          <Card className="welcome-card" padding="large">
            <h2>Welcome to Form Seva</h2>
            <p className="welcome-text">
              Fill complex government and bank forms easily in your local language. 
              Simply upload a photo or scan of your form, answer simple questions in 
              Hindi or Marathi, and we'll help you complete it!
            </p>
            
            <div className="features-list">
              <div className="feature-item">
                <span className="feature-icon">📷</span>
                <span>Upload form image or PDF</span>
              </div>
              <div className="feature-item">
                <span className="feature-icon">💬</span>
                <span>Answer questions in your language</span>
              </div>
              <div className="feature-item">
                <span className="feature-icon">✅</span>
                <span>Get annotated form ready to submit</span>
              </div>
            </div>

            <div className="cta-section">
              <Button 
                variant="primary" 
                size="large" 
                onClick={handleStartFilling}
                icon="→"
              >
                शुरू करें / Start Filling Form
              </Button>
            </div>
          </Card>
        </div>

        <div className="supported-forms">
          <h3>Supported Forms</h3>
          <div className="forms-grid">
            <Card hoverable>
              <span className="form-icon">🏦</span>
              <h4>Bank KYC</h4>
              <p>Know Your Customer forms</p>
            </Card>
            <Card hoverable>
              <span className="form-icon">🪪</span>
              <h4>Aadhaar</h4>
              <p>Aadhaar registration/updates</p>
            </Card>
            <Card hoverable>
              <span className="form-icon">🏛️</span>
              <h4>Government</h4>
              <p>Various government forms</p>
            </Card>
            <Card hoverable>
              <span className="form-icon">📝</span>
              <h4>Others</h4>
              <p>Any printed form</p>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}

export default HomePage;
