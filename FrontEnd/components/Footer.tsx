import React from 'react';
import './Footer.css';

const Footer: React.FC = () => {
  return (
    <div className="bottom-nav">
      <div className="nav-item active">
        <div className="nav-icon">
          <img src="/icons/홈화면_홈.png" alt="홈" />
        </div>
        <span className="nav-label">홈</span>
      </div>
      <div className="nav-item">
        <div className="nav-icon">
          <img src="/icons/홈화면_영상.png" alt="영상" />
        </div>
        <span className="nav-label">영상</span>
      </div>
      <div className="nav-item">
        <div className="nav-icon">
          <img src="/icons/홈화면_달력.png" alt="달력" />
        </div>
        <span className="nav-label">달력</span>
      </div>
      <div className="nav-item">
        <div className="nav-icon">
          <img src="/icons/홈화면_가이드.png" alt="가이드" />
        </div>
        <span className="nav-label">가이드</span>
      </div>
      <div className="nav-item">
        <div className="nav-icon">
          <img src="/icons/홈화면_설정.png" alt="설정" />
        </div>
        <span className="nav-label">설정</span>
      </div>
    </div>
  );
};

export default Footer;

