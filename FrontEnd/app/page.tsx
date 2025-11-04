'use client';

import { useState } from 'react';
import SplashScreen from '@/screens/SplashScreen';
import LoginScreen from '@/screens/LoginScreen';
import SignUpScreen from '@/screens/SignUpScreen';
import MainScreen from '@/screens/MainScreen';
import TodayConversationDetailScreen from '@/screens/TodayConversationDetailScreen';
import DailyReportScreen from '@/screens/DailyReportScreen';
import VideoScreen from '@/screens/VideoScreen';
import RegisterChildScreen from '@/screens/RegisterChildScreen';
import CalendarScreen from '@/screens/CalendarScreen';
import SettingsScreen from '@/screens/SettingsScreen';
import ChangeChildProfileScreen from '@/screens/ChangeChildProfileScreen';
import ChangePasswordScreen from '@/screens/ChangePasswordScreen';
import LogoutConfirmScreen from '@/screens/LogoutConfirmScreen';
import DeleteAccountScreen from '@/screens/DeleteAccountScreen';

export default function Home() {
  const [currentScreen, setCurrentScreen] = useState<'splash' | 'login' | 'signup' | 'main' | 'conversation-detail' | 'daily-report' | 'video' | 'register-child' | 'calendar' | 'settings' | 'change-child-profile' | 'change-password' | 'logout-confirm' | 'delete-account'>('splash');
  const [hasChild, setHasChild] = useState(false); // 아이 등록 여부

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
    setCurrentScreen('calendar');
  };

  const handleGuide = () => {
    console.log('가이드 페이지로 이동');
    // TODO: 가이드 페이지 구현
  };

  const handleSettings = () => {
    console.log('설정 페이지로 이동');
    setCurrentScreen('settings');
  };

  const handleRegisterChild = () => {
    console.log('아이 등록 페이지로 이동');
    setCurrentScreen('register-child');
  };

  const handleRegisterChildComplete = () => {
    console.log('아이 등록 완료');
    setHasChild(true);
    setCurrentScreen('main');
  };

  if (currentScreen === 'splash') {
    return <SplashScreen onLogin={handleLogin} onSignUp={handleSignUp} />;
  }

  if (currentScreen === 'login') {
    return <LoginScreen onBack={handleBackToSplash} onLoginComplete={handleLoginComplete} onSignUp={handleSignUp} />;
  }

  if (currentScreen === 'signup') {
    return <SignUpScreen onBack={handleBackToSplash} onSignUpComplete={handleSignUpComplete} onLogin={handleLogin} />;
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

  if (currentScreen === 'calendar') {
    return <CalendarScreen 
      onHome={() => setCurrentScreen('main')}
      onVideo={handleVideo}
      onCalendar={handleCalendar}
      onGuide={handleGuide}
      onSettings={handleSettings}
    />;
  }

  if (currentScreen === 'register-child') {
    return <RegisterChildScreen 
      onBack={handleBackToMain}
      onRegisterComplete={handleRegisterChildComplete}
      onVideo={handleVideo}
      onCalendar={handleCalendar}
      onGuide={handleGuide}
      onSettings={handleSettings}
    />;
  }

  if (currentScreen === 'settings') {
    return <SettingsScreen 
      onHome={() => setCurrentScreen('main')}
      onVideo={handleVideo}
      onCalendar={handleCalendar}
      onGuide={handleGuide}
      onSettings={handleSettings}
      onLogout={() => setCurrentScreen('logout-confirm')}
      onProfileChange={() => setCurrentScreen('change-child-profile')}
      onPasswordChange={() => setCurrentScreen('change-password')}
      onAccountDelete={() => setCurrentScreen('delete-account')}
    />;
  }

  if (currentScreen === 'change-child-profile') {
    return <ChangeChildProfileScreen 
      onBack={() => setCurrentScreen('settings')}
      onHome={() => setCurrentScreen('main')}
      onVideo={handleVideo}
      onCalendar={handleCalendar}
      onGuide={handleGuide}
      onSettings={handleSettings}
      onSave={() => {
        console.log('프로필 저장 완료');
      }}
    />;
  }

  if (currentScreen === 'change-password') {
    return <ChangePasswordScreen 
      onBack={() => setCurrentScreen('settings')}
      onHome={() => setCurrentScreen('main')}
      onVideo={handleVideo}
      onCalendar={handleCalendar}
      onGuide={handleGuide}
      onSettings={handleSettings}
      onSave={() => {
        console.log('비밀번호 변경 완료');
      }}
    />;
  }

  if (currentScreen === 'logout-confirm') {
    return <LogoutConfirmScreen 
      onBack={() => setCurrentScreen('settings')}
      onHome={() => setCurrentScreen('main')}
      onVideo={handleVideo}
      onCalendar={handleCalendar}
      onGuide={handleGuide}
      onSettings={handleSettings}
      onConfirm={handleLogout}
    />;
  }

  if (currentScreen === 'delete-account') {
    return <DeleteAccountScreen 
      onBack={() => setCurrentScreen('settings')}
      onHome={() => setCurrentScreen('main')}
      onVideo={handleVideo}
      onCalendar={handleCalendar}
      onGuide={handleGuide}
      onSettings={handleSettings}
      onConfirm={handleLogout}
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
    onRegisterChild={handleRegisterChild}
    hasChild={hasChild}
  />;
}
