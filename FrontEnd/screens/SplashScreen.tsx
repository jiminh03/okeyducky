import React from 'react';
import '@/screens/SplashScreen.css';

interface SplashScreenProps {
  onLogin: () => void;
  onSignUp: () => void;
}

const SplashScreen: React.FC<SplashScreenProps> = ({ onLogin, onSignUp }) => {
  return (
    <div className="splash-container">
      {/* 메인 콘텐츠 */}
      <div className="main-content">
        <div className="logo-container">
          {/* 오키더키 폰트 이미지 */}
          <img 
            src="/logos/오키더키 폰트.png" 
            alt="오키더키" 
            className="title-img"
          />
          
          <div className="duck-logo">
            {/* 오리 로고 - PNG 이미지 */}
            <img 
              src="/logos/오키더키 로고.png" 
              alt="오키더키 로고" 
              className="duck-img"
            />
          </div>
        </div>
      </div>

      {/* 하단 버튼들 */}
      <div className="button-container">
        <button className="login-btn" onClick={onLogin}>
          로그인
        </button>
        <button className="signup-btn" onClick={onSignUp}>
          회원가입
        </button>
      </div>
    </div>
  );
};

export default SplashScreen;