'use client';

import { useState } from 'react';
import SplashScreen from '@/screens/SplashScreen';
import LoginScreen from '@/screens/LoginScreen';
import SignUpScreen from '@/screens/SignUpScreen';
import MainScreen from '@/screens/MainScreen';
import TodayConversationDetailScreen from '@/screens/TodayConversationDetailScreen';

export default function Home() {
  const [currentScreen, setCurrentScreen] = useState<'splash' | 'login' | 'signup' | 'main' | 'conversation-detail'>('splash');

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

  const handleLogout = () => {
    console.log('로그아웃');
    setCurrentScreen('splash');
  };

  const handleConversationDetail = () => {
    console.log('오늘 대화 상세 보기');
    setCurrentScreen('conversation-detail');
  };

  const handleBackToMain = () => {
    console.log('메인으로 돌아가기');
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

  if (currentScreen === 'conversation-detail') {
    return <TodayConversationDetailScreen onBack={handleBackToMain} />;
  }

  return <MainScreen onLogout={handleLogout} onConversationDetail={handleConversationDetail} />;
}
