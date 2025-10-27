import React, { useState } from 'react';
import SplashScreen from './components/SplashScreen';
import SignUpScreen from './components/SignUpScreen';
import './App.css';

function App() {
  const [currentScreen, setCurrentScreen] = useState<'splash' | 'signup' | 'main'>('splash');

  const handleLogin = () => {
    console.log('로그인 버튼 클릭');
    // 로그인 로직 구현
    setCurrentScreen('main');
  };

  const handleSignUp = () => {
    console.log('회원가입 버튼 클릭');
    // 회원가입 화면으로 이동
    setCurrentScreen('signup');
  };

  const handleBackToSplash = () => {
    setCurrentScreen('splash');
  };

  const handleSignUpComplete = () => {
    console.log('회원가입 완료');
    setCurrentScreen('main');
  };

  if (currentScreen === 'splash') {
    return <SplashScreen onLogin={handleLogin} onSignUp={handleSignUp} />;
  }

  if (currentScreen === 'signup') {
    return <SignUpScreen onBack={handleBackToSplash} onSignUpComplete={handleSignUpComplete} />;
  }

  return (
    <div className="main-app">
      <h1>오키더키 메인 화면</h1>
      <p>스플래시 화면에서 로그인 또는 회원가입을 완료했습니다!</p>
      <button onClick={() => setCurrentScreen('splash')}>
        스플래시 화면으로 돌아가기
      </button>
    </div>
  );
}

export default App;
