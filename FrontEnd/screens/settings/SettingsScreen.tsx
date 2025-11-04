import React from 'react';
import Header from '@/components/Header';
import Footer from '@/components/Footer';
import './SettingsScreen.css';

interface SettingsScreenProps {
  onHome?: () => void;
  onVideo?: () => void;
  onCalendar?: () => void;
  onGuide?: () => void;
  onSettings?: () => void;
  onLogout?: () => void;
  onProfileChange?: () => void;
  onPasswordChange?: () => void;
  onAccountDelete?: () => void;
}

const SettingsScreen: React.FC<SettingsScreenProps> = ({
  onHome,
  onVideo,
  onCalendar,
  onGuide,
  onSettings,
  onLogout,
  onProfileChange,
  onPasswordChange,
  onAccountDelete
}) => {
  return (
    <div className="settings-screen">
      {/* 상단 헤더 */}
      <Header />

      {/* 메인 콘텐츠 */}
      <div className="settings-content-area">
        <div className="settings-list">
          <div 
            className="settings-item"
            onClick={onProfileChange}
          >
            <span className="settings-item-text">아이 프로필 변경</span>
            <span className="settings-item-arrow">{'>'}</span>
          </div>
          <div 
            className="settings-item"
            onClick={onPasswordChange}
          >
            <span className="settings-item-text">비밀번호 변경</span>
            <span className="settings-item-arrow">{'>'}</span>
          </div>
          <div 
            className="settings-item"
            onClick={onLogout}
          >
            <span className="settings-item-text">로그아웃</span>
            <span className="settings-item-arrow">{'>'}</span>
          </div>
          <div 
            className="settings-item"
            onClick={onAccountDelete}
          >
            <span className="settings-item-text">계정 탈퇴</span>
            <span className="settings-item-arrow">{'>'}</span>
          </div>
        </div>
      </div>

      {/* 하단 네비게이션 */}
      <Footer 
        activeTab="settings"
        onHome={onHome}
        onVideo={onVideo}
        onCalendar={onCalendar}
        onGuide={onGuide}
        onSettings={onSettings}
      />
    </div>
  );
};

export default SettingsScreen;

