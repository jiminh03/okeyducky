import React from 'react';
import DetailHeader from '@/components/DetailHeader';
import Footer from '@/components/Footer';
import './LogoutConfirmScreen.css';

interface LogoutConfirmScreenProps {
  onBack: () => void;
  onHome?: () => void;
  onVideo?: () => void;
  onCalendar?: () => void;
  onGuide?: () => void;
  onSettings?: () => void;
  onConfirm?: () => void;
}

const LogoutConfirmScreen: React.FC<LogoutConfirmScreenProps> = ({
  onBack,
  onHome,
  onVideo,
  onCalendar,
  onGuide,
  onSettings,
  onConfirm
}) => {
  const handleLogout = () => {
    console.log('로그아웃 처리');
    onConfirm?.();
  };

  return (
    <div className="logout-confirm-container">
      {/* 상단 헤더 */}
      <DetailHeader title="로그아웃" onBack={onBack} />

      {/* 메인 콘텐츠 */}
      <div className="logout-confirm-content">
        <div className="logout-confirm-box">
          <div className="logout-icon">👋</div>
          <h2 className="logout-title">로그아웃 하시겠습니까?</h2>
          <p className="logout-message">
            로그아웃 후에는 다시 로그인해야 합니다.
          </p>

          <div className="logout-buttons">
            <button
              className="cancel-btn"
              onClick={onBack}
            >
              취소
            </button>
            <button
              className="logout-btn"
              onClick={handleLogout}
            >
              로그아웃
            </button>
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

export default LogoutConfirmScreen;

