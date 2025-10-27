import React, { useState } from 'react';
import './SignUpScreen.css';

interface SignUpScreenProps {
  onBack: () => void;
  onSignUpComplete: () => void;
}

const SignUpScreen: React.FC<SignUpScreenProps> = ({ onBack, onSignUpComplete }) => {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: ''
  });

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    console.log('회원가입 데이터:', formData);
    // 회원가입 로직 구현
    onSignUpComplete();
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
        <h1 className="signup-brand-title">오키더키</h1>
        <h2 className="signup-page-title">회원가입</h2>

        {/* 회원가입 폼 */}
        <form onSubmit={handleSubmit} className="signup-form">
          {/* 이름 */}
          <div className="form-group">
            <label className="form-label">이름</label>
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
            <label className="form-label">아이디(이메일)</label>
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
            <label className="form-label">비밀번호</label>
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
            <label className="form-label">비밀번호 확인</label>
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
          <button type="submit" className="signup-submit-btn">
            회원가입
          </button>
        </form>

        {/* 하단 로그인 링크 */}
        <div className="login-link-section">
          <span className="login-text">이미 계정이 있으신가요?</span>
          <button className="login-link-btn" onClick={onBack}>
            로그인하기
          </button>
        </div>
      </div>
    </div>
  );
};

export default SignUpScreen;
