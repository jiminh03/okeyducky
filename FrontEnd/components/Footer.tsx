import React from 'react';
import './Footer.css';

const Footer: React.FC = () => {
  return (
    <div className="bottom-nav">
      <div className="nav-item active">
        <span className="nav-icon">🏠</span>
        <span className="nav-label">홈</span>
      </div>
      <div className="nav-item">
        <span className="nav-icon">🎥</span>
        <span className="nav-label">영상</span>
      </div>
      <div className="nav-item">
        <span className="nav-icon">📅</span>
        <span className="nav-label">달력</span>
      </div>
      <div className="nav-item">
        <span className="nav-icon">📖</span>
        <span className="nav-label">가이드</span>
      </div>
      <div className="nav-item">
        <span className="nav-icon">⚙️</span>
        <span className="nav-label">설정</span>
      </div>
    </div>
  );
};

export default Footer;

