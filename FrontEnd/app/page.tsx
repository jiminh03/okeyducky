'use client';

import { useState } from 'react';
import SplashScreen from '@/screens/SplashScreen';
import LoginScreen from '@/screens/LoginScreen';
import SignUpScreen from '@/screens/SignUpScreen';
import MainScreen from '@/screens/MainScreen';
import TodayConversationDetailScreen from '@/screens/TodayConversationDetailScreen';
import DailyReportScreen from '@/screens/DailyReportScreen';
import VideoScreen from '@/screens/VideoScreen';

export default function Home() {
  const [currentScreen, setCurrentScreen] = useState<'splash' | 'login' | 'signup' | 'main' | 'conversation-detail' | 'daily-report' | 'video'>('splash');

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

  const handleDailyReport = () => {
    console.log('일일 리포트 상세 보기');
    setCurrentScreen('daily-report');
  };

  const handleVideo = () => {
    console.log('영상 페이지로 이동');
    setCurrentScreen('video');
  };

  const handleCalendar = () => {
    console.log('달력 페이지로 이동');
    // TODO: 달력 페이지 구현
  };

  const handleGuide = () => {
    console.log('가이드 페이지로 이동');
    // TODO: 가이드 페이지 구현
  };

  const handleSettings = () => {
    console.log('설정 페이지로 이동');
    // TODO: 설정 페이지 구현
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
    return <TodayConversationDetailScreen 
      onBack={handleBackToMain}
      onHome={() => setCurrentScreen('main')}
      onVideo={handleVideo}
      onCalendar={handleCalendar}
      onGuide={handleGuide}
      onSettings={handleSettings}
    />;
  }

  if (currentScreen === 'daily-report') {
    return <DailyReportScreen 
      onBack={handleBackToMain}
      onHome={() => setCurrentScreen('main')}
      onVideo={handleVideo}
      onCalendar={handleCalendar}
      onGuide={handleGuide}
      onSettings={handleSettings}
    />;
  }

  if (currentScreen === 'video') {
    return <VideoScreen 
      onHome={() => setCurrentScreen('main')}
      onVideo={handleVideo}
      onCalendar={handleCalendar}
      onGuide={handleGuide}
      onSettings={handleSettings}
    />;
  }

  return <MainScreen 
    onLogout={handleLogout} 
    onConversationDetail={handleConversationDetail} 
    onDailyReport={handleDailyReport}
    onVideo={handleVideo}
    onCalendar={handleCalendar}
    onGuide={handleGuide}
    onSettings={handleSettings}
  />;
}
