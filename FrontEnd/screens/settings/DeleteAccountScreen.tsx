import React, { useState } from 'react';
import DetailHeader from '@/components/DetailHeader';
import Footer from '@/components/Footer';
import './DeleteAccountScreen.css';

interface DeleteAccountScreenProps {
  onBack: () => void;
  onHome?: () => void;
  onVideo?: () => void;
  onCalendar?: () => void;
  onGuide?: () => void;
  onSettings?: () => void;
  onConfirm?: () => void;
}

const DeleteAccountScreen: React.FC<DeleteAccountScreenProps> = ({
  onBack,
  onHome,
  onVideo,
  onCalendar,
  onGuide,
  onSettings,
  onConfirm
}) => {
  const [confirmText, setConfirmText] = useState('');
  const [isConfirmed, setIsConfirmed] = useState(false);
  const requiredText = '탈퇴';

  const handleConfirmTextChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setConfirmText(value);
    setIsConfirmed(value === requiredText);
  };

  const handleDelete = () => {
    if (isConfirmed) {
      console.log('계정 탈퇴 처리');
      onConfirm?.();
      // 실제로는 로그아웃 처리 후 스플래시 화면으로 이동
    }
  };

  return (
    <div className="delete-account-container">
      {/* 상단 헤더 */}
      <DetailHeader title="계정 탈퇴" onBack={onBack} />

      {/* 메인 콘텐츠 */}
      <div className="delete-account-content">
        <div className="delete-account-warning">
          <div className="warning-icon">⚠️</div>
          <h2 className="warning-title">계정 탈퇴 시 주의사항</h2>
          <ul className="warning-list">
            <li>모든 데이터가 영구적으로 삭제됩니다</li>
            <li>삭제된 데이터는 복구할 수 없습니다</li>
            <li>아이의 대화 기록과 리포트가 모두 삭제됩니다</li>
            <li>등록된 아이 정보도 삭제됩니다</li>
          </ul>
        </div>

        <div className="delete-account-confirm">
          <p className="confirm-instruction">
            계정 탈퇴를 진행하시려면 아래에 <strong>"{requiredText}"</strong>를 입력해주세요.
          </p>
          <input
            type="text"
            className={`confirm-input ${isConfirmed ? 'confirmed' : ''}`}
            placeholder={requiredText}
            value={confirmText}
            onChange={handleConfirmTextChange}
          />
        </div>

        <button
          className={`delete-account-btn ${isConfirmed ? 'enabled' : 'disabled'}`}
          onClick={handleDelete}
          disabled={!isConfirmed}
        >
          계정 탈퇴하기
        </button>
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

export default DeleteAccountScreen;

