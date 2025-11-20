import React, { useState } from 'react';
import DetailHeader from '@/components/DetailHeader';
import Footer from '@/components/Footer';
import { userApi } from '@/services/api';
import './ChangePasswordScreen.css';

interface ChangePasswordScreenProps {
  onBack: () => void;
  onHome?: () => void;
  onVideo?: () => void;
  onCalendar?: () => void;
  onGuide?: () => void;
  onSettings?: () => void;
  onSave?: () => void;
}

const ChangePasswordScreen: React.FC<ChangePasswordScreenProps> = ({
  onBack,
  onHome,
  onVideo,
  onCalendar,
  onGuide,
  onSettings,
  onSave
}) => {
  const [formData, setFormData] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: ''
  });

  const [errors, setErrors] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: ''
  });
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string>('');

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    // 에러 초기화
    setErrors(prev => ({
      ...prev,
      [name]: ''
    }));
  };

  const validateForm = () => {
    const newErrors = {
      currentPassword: '',
      newPassword: '',
      confirmPassword: ''
    };

    if (!formData.currentPassword) {
      newErrors.currentPassword = '현재 비밀번호를 입력해주세요';
    }

    if (!formData.newPassword) {
      newErrors.newPassword = '새 비밀번호를 입력해주세요';
    } else if (formData.newPassword.length < 8) {
      newErrors.newPassword = '비밀번호는 8자 이상이어야 합니다';
    }

    if (!formData.confirmPassword) {
      newErrors.confirmPassword = '비밀번호 확인을 입력해주세요';
    } else if (formData.newPassword !== formData.confirmPassword) {
      newErrors.confirmPassword = '비밀번호가 일치하지 않습니다';
    }

    setErrors(newErrors);
    return !Object.values(newErrors).some(error => error !== '');
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage('');
    
    if (!validateForm()) {
      return;
    }

    setIsLoading(true);

    try {
      // API 호출: 비밀번호만 변경
      const response = await userApi.updateMe({
        password: formData.newPassword,
      });

      if (response.success) {
        console.log('비밀번호 변경 성공:', response.data);
        onSave?.();
        onBack();
      } else {
        setErrorMessage(response.message || '비밀번호 변경에 실패했습니다.');
      }
    } catch (error) {
      console.error('비밀번호 변경 오류:', error);
      setErrorMessage('비밀번호 변경 중 오류가 발생했습니다.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="change-password-container">
      {/* 상단 헤더 */}
      <DetailHeader title="비밀번호 변경" onBack={onBack} />

      {/* 메인 콘텐츠 */}
      <div className="change-password-content">
        <form className="change-password-form" onSubmit={handleSubmit}>
          {/* 에러 메시지 */}
          {errorMessage && (
            <div className="error-message" style={{
              color: '#ff4444',
              fontSize: '14px',
              marginBottom: '16px',
              textAlign: 'center',
              padding: '12px',
              backgroundColor: '#fff5f5',
              borderRadius: '8px',
              border: '1px solid #ffcccc'
            }}>
              {errorMessage}
            </div>
          )}

          {/* 현재 비밀번호 */}
          <div className="form-group">
            <label className="form-label">현재 비밀번호</label>
            <input
              type="password"
              name="currentPassword"
              className={`form-input ${errors.currentPassword ? 'error' : ''}`}
              placeholder="현재 비밀번호를 입력해주세요"
              value={formData.currentPassword}
              onChange={handleInputChange}
              required
            />
            {errors.currentPassword && (
              <span className="error-message">{errors.currentPassword}</span>
            )}
          </div>

          {/* 새 비밀번호 */}
          <div className="form-group">
            <label className="form-label">새 비밀번호</label>
            <input
              type="password"
              name="newPassword"
              className={`form-input ${errors.newPassword ? 'error' : ''}`}
              placeholder="새 비밀번호를 입력해주세요 (8자 이상)"
              value={formData.newPassword}
              onChange={handleInputChange}
              required
            />
            {errors.newPassword && (
              <span className="error-message">{errors.newPassword}</span>
            )}
          </div>

          {/* 새 비밀번호 확인 */}
          <div className="form-group">
            <label className="form-label">새 비밀번호 확인</label>
            <input
              type="password"
              name="confirmPassword"
              className={`form-input ${errors.confirmPassword ? 'error' : ''}`}
              placeholder="새 비밀번호를 다시 입력해주세요"
              value={formData.confirmPassword}
              onChange={handleInputChange}
              required
            />
            {errors.confirmPassword && (
              <span className="error-message">{errors.confirmPassword}</span>
            )}
          </div>

          {/* 저장 버튼 */}
          <button 
            type="submit" 
            className="save-password-btn"
            disabled={isLoading}
          >
            {isLoading ? '처리 중...' : '비밀번호 변경'}
          </button>
        </form>
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

export default ChangePasswordScreen;

