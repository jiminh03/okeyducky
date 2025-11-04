import React, { useState } from 'react';
import { authApi } from '@/services/api';
import './SignUpScreen.css';

interface SignUpScreenProps {
  onBack: () => void;
  onSignUpComplete: () => void;
  onLogin: () => void;
}

const SignUpScreen: React.FC<SignUpScreenProps> = ({ onBack, onSignUpComplete, onLogin }) => {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: ''
  });
  const [error, setError] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    // 에러 메시지 초기화
    if (error) {
      setError('');
    }
  };

  const validateForm = (): boolean => {
    // 이름 검증
    if (!formData.name.trim()) {
      setError('이름을 입력해주세요.');
      return false;
    }

    // 이메일 검증
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!formData.email.trim()) {
      setError('이메일을 입력해주세요.');
      return false;
    }
    if (!emailRegex.test(formData.email)) {
      setError('올바른 이메일 형식을 입력해주세요.');
      return false;
    }

    // 비밀번호 검증
    if (!formData.password) {
      setError('비밀번호를 입력해주세요.');
      return false;
    }
    if (formData.password.length < 6) {
      setError('비밀번호는 최소 6자 이상이어야 합니다.');
      return false;
    }

    // 비밀번호 확인 검증
    if (formData.password !== formData.confirmPassword) {
      setError('비밀번호가 일치하지 않습니다.');
      return false;
    }

    return true;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    // 폼 검증
    if (!validateForm()) {
      return;
    }

    setIsLoading(true);

    try {
      const response = await authApi.register({
        parent_name: formData.name.trim(),
        email: formData.email.trim(),
        password: formData.password,
      });

      if (response.success) {
        console.log('회원가입 성공:', response.data);
        onSignUpComplete();
      } else {
        setError(response.message || '회원가입에 실패했습니다.');
      }
    } catch (error) {
      console.error('회원가입 오류:', error);
      setError('회원가입 중 오류가 발생했습니다.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="signup-container">
      {/* 상단 네비게이션 */}
      <div className="signup-header">
        <button className="back-btn" onClick={onBack}>
          ←
        </button>
        <div className="header-spacer"></div>
      </div>

      {/* 메인 콘텐츠 */}
      <div className="signup-content">
        {/* 오키더키 로고 */}
        <div className="signup-logo">
          <img 
            src="/logos/오키더키 폰트.png" 
            alt="오키더키" 
            className="signup-title-img"
          />
        </div>

        {/* 페이지 제목 */}
        <h2 className="signup-page-title">회원가입</h2>

        {/* 회원가입 폼 */}
        <form onSubmit={handleSubmit} className="signup-form">
          {/* 에러 메시지 */}
          {error && (
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
              {error}
            </div>
          )}

          {/* 이름 */}
          <div className="form-group">
            <label className="form-label">이름 <span className="required-star">*</span></label>
            <input
              type="text"
              name="name"
              value={formData.name}
              onChange={handleInputChange}
              className="form-input"
              placeholder="이름을 입력해주세요"
              required
            />
          </div>

          {/* 아이디(이메일) */}
          <div className="form-group">
            <label className="form-label">아이디(이메일) <span className="required-star">*</span></label>
            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleInputChange}
              className="form-input"
              placeholder="이메일을 입력해주세요"
              required
            />
          </div>

          {/* 비밀번호 */}
          <div className="form-group">
            <label className="form-label">비밀번호 <span className="required-star">*</span></label>
            <input
              type="password"
              name="password"
              value={formData.password}
              onChange={handleInputChange}
              className="form-input"
              placeholder="최소 6자 이상 입력해주세요"
              required
            />
          </div>

          {/* 비밀번호 확인 */}
          <div className="form-group">
            <label className="form-label">비밀번호 확인 <span className="required-star">*</span></label>
            <input
              type="password"
              name="confirmPassword"
              value={formData.confirmPassword}
              onChange={handleInputChange}
              className="form-input"
              placeholder="비밀번호를 한 번 더 입력해주세요"
              required
            />
          </div>

          {/* 회원가입 버튼 */}
          <button 
            type="submit" 
            className="signup-submit-btn"
            disabled={isLoading}
          >
            {isLoading ? '처리 중...' : '회원가입'}
          </button>
        </form>

        {/* 하단 로그인 링크 */}
        <div className="login-link-section">
          <span className="login-text">이미 계정이 있으신가요?</span>
          <button className="login-link-btn" onClick={onLogin}>
            로그인하기
          </button>
        </div>
      </div>
    </div>
  );
};

export default SignUpScreen;