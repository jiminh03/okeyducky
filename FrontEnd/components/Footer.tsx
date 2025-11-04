import React from 'react';
import './Footer.css';

interface FooterProps {
  activeTab?: 'home' | 'video' | 'calendar' | 'guide' | 'settings';
  onHome?: () => void;
  onVideo?: () => void;
  onCalendar?: () => void;
  onGuide?: () => void;
  onSettings?: () => void;
}

const Footer: React.FC<FooterProps> = ({ 
  activeTab = 'home',
  onHome,
  onVideo,
  onCalendar,
  onGuide,
  onSettings
}) => {
  // 페이지별로 다른 아이콘 세트 사용
  let iconPrefix = '홈화면'; // 기본값
  if (activeTab === 'video') {
    iconPrefix = '영상화면';
  } else if (activeTab === 'calendar') {
    iconPrefix = '달력화면';
  }
  
  return (
    <div className="bottom-nav">
      <div 
        className={`nav-item ${activeTab === 'home' ? 'active' : ''}`}
        onClick={onHome}
      >
        <div className="nav-icon">
          <img src={`/icons/${iconPrefix}_홈.png`} alt="홈" />
        </div>
        <span className="nav-label">홈</span>
      </div>
      <div 
        className={`nav-item ${activeTab === 'video' ? 'active' : ''}`}
        onClick={onVideo}
      >
        <div className="nav-icon">
          <img src={`/icons/${iconPrefix}_영상.png`} alt="영상" />
        </div>
        <span className="nav-label">영상</span>
      </div>
      <div 
        className={`nav-item ${activeTab === 'calendar' ? 'active' : ''}`}
        onClick={onCalendar}
      >
        <div className="nav-icon">
          <img src={`/icons/${iconPrefix}_달력.png`} alt="달력" />
        </div>
        <span className="nav-label">달력</span>
      </div>
      <div 
        className={`nav-item ${activeTab === 'guide' ? 'active' : ''}`}
        onClick={onGuide}
      >
        <div className="nav-icon">
          <img src={`/icons/${iconPrefix}_가이드.png`} alt="가이드" />
        </div>
        <span className="nav-label">가이드</span>
      </div>
      <div 
        className={`nav-item ${activeTab === 'settings' ? 'active' : ''}`}
        onClick={onSettings}
      >
        <div className="nav-icon">
          <img src={`/icons/${iconPrefix}_설정.png`} alt="설정" />
        </div>
        <span className="nav-label">설정</span>
      </div>
    </div>
  );
};

export default Footer;

