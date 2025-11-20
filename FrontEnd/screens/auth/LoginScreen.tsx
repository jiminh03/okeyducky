import React, { useState } from 'react';
import './LoginScreen.css';
import { authApi } from '../../services/api';

interface LoginScreenProps {
  onBack: () => void;
  onLoginComplete: () => void;
  onSignUp: () => void;
  message?: string | null;
}

const LoginScreen: React.FC<LoginScreenProps> = ({ onBack, onLoginComplete, onSignUp, message }) => {
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    if (error) {
      setError(null);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (loading) return;

    setLoading(true);
    setError(null);

    try {
      const result = await authApi.login(formData);

      if (!result.success || !result.data || !result.data.access_token) {
        setError(result.message || '로그인에 실패했습니다. 다시 시도해주세요.');
        return;
      }

      const { access_token, refresh_token } = result.data;
      localStorage.setItem('access_token', access_token);
      if (refresh_token) {
        localStorage.setItem('refresh_token', refresh_token);
      }

      onLoginComplete();
    } catch (err) {
      const message = err instanceof Error ? err.message : '로그인에 실패했습니다.';
      setError(message);
    } finally {
      setLoading(false);
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
          {message && (
            <p
              className="form-info"
              style={{ color: '#2a7de1', fontSize: '14px', marginBottom: '12px', textAlign: 'center' }}
            >
              {message}
            </p>
          )}
          {error && <p className="form-error">{error}</p>}
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
          <button type="submit" className="login-submit-btn" disabled={loading}>
            {loading ? '로그인 중...' : '로그인'}
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

