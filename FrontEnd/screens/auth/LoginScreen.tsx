import React, { useState } from 'react';
import { authApi } from '@/services/api';
import './LoginScreen.css';

interface LoginScreenProps {
  onBack: () => void;
  onLoginComplete: () => void;
  onSignUp: () => void;
}

const LoginScreen: React.FC<LoginScreenProps> = ({ onBack, onLoginComplete, onSignUp }) => {
  const [formData, setFormData] = useState({
    email: '',
    password: ''
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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    // 기본 검증
    if (!formData.email.trim()) {
      setError('이메일을 입력해주세요.');
      return;
    }

    if (!formData.password) {
      setError('비밀번호를 입력해주세요.');
      return;
    }

    setIsLoading(true);

    try {
      const response = await authApi.login({
        email: formData.email.trim(),
        password: formData.password,
      });

      if (response.success) {
        console.log('로그인 성공:', response.data);
        onLoginComplete();
      } else {
        setError(response.message || '로그인에 실패했습니다.');
      }
    } catch (error) {
      console.error('로그인 오류:', error);
      setError('로그인 중 오류가 발생했습니다.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="login-container">
      {/* 상단 네비게이션 */}
      <div className="login-header">
        <button className="back-btn" onClick={onBack}>
          ←
        </button>
        <div className="header-spacer"></div>
      </div>

      {/* 메인 콘텐츠 */}
      <div className="login-content">
        {/* 오키더키 로고 */}
        <div className="login-logo">
          <img 
            src="/logos/오키더키 폰트.png" 
            alt="오키더키" 
            className="login-title-img"
          />
        </div>

        {/* 브랜드 제목 */}
        <h1 className="login-brand-title">오키더키</h1>

        {/* 페이지 제목 */}
        {/* <h2 className="login-page-title">로그인</h2> */}

        {/* 로그인 폼 */}
        <form onSubmit={handleSubmit} className="login-form">
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

          {/* 아이디(이메일) */}
          <div className="form-group">
            <label className="form-label">아이디(이메일)</label>
            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleInputChange}
              className="form-input"
              placeholder="아이디를 입력해주세요"
              required
            />
          </div>

          {/* 비밀번호 */}
          <div className="form-group">
            <label className="form-label">비밀번호</label>
            <input
              type="password"
              name="password"
              value={formData.password}
              onChange={handleInputChange}
              className="form-input"
              placeholder="비밀번호를 입력해주세요"
              required
            />
          </div>

          {/* 로그인 버튼 */}
          <button 
            type="submit" 
            className="login-submit-btn"
            disabled={isLoading}
          >
            {isLoading ? '처리 중...' : '로그인'}
          </button>
        </form>

        {/* 하단 회원가입 링크 */}
        <div className="signup-link-section">
          <span className="signup-text">계정이 없으신가요?</span>
          <button className="signup-link-btn" onClick={onSignUp}>
            회원가입
          </button>
        </div>
      </div>
    </div>
  );
};

export default LoginScreen;

