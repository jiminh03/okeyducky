'use client';

import { useState } from 'react';
import SplashScreen from '@/components/SplashScreen';
import LoginScreen from '@/components/LoginScreen';
import SignUpScreen from '@/components/SignUpScreen';

export default function Home() {
  const [currentScreen, setCurrentScreen] = useState<'splash' | 'login' | 'signup' | 'main'>('splash');

  const handleLogin = () => {
    console.log('로그인 버튼 클릭');
    setCurrentScreen('login');
  };

  const handleSignUp = () => {
    console.log('회원가입 버튼 클릭');
    setCurrentScreen('signup');
  };

  const handleBackToSplash = () => {
    setCurrentScreen('splash');
  };

  const handleLoginComplete = () => {
    console.log('로그인 완료');
    setCurrentScreen('main');
  };

  const handleSignUpComplete = () => {
    console.log('회원가입 완료');
    setCurrentScreen('main');
  };

  if (currentScreen === 'splash') {
    return <SplashScreen onLogin={handleLogin} onSignUp={handleSignUp} />;
  }

  if (currentScreen === 'login') {
    return <LoginScreen onBack={handleBackToSplash} onLoginComplete={handleLoginComplete} onSignUp={handleSignUp} />;
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
