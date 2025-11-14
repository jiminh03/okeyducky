'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import SplashScreen from '@/screens/auth/SplashScreen';
import LoginScreen from '@/screens/auth/LoginScreen';
import SignUpScreen from '@/screens/auth/SignUpScreen';
import MainScreen from '@/screens/home/MainScreen';
import TodayConversationDetailScreen from '@/screens/home/TodayConversationDetailScreen';
import DailyReportScreen from '@/screens/home/DailyReportScreen';
import VideoScreen from '@/screens/streaming/VideoScreen';
import RegisterChildScreen from '@/screens/home/RegisterChildScreen';
import CalendarScreen from '@/screens/calendar/CalendarScreen';
import SettingsScreen from '@/screens/settings/SettingsScreen';
import ChangeChildProfileScreen from '@/screens/settings/ChangeChildProfileScreen';
import ChangePasswordScreen from '@/screens/settings/ChangePasswordScreen';
import LogoutConfirmScreen from '@/screens/settings/LogoutConfirmScreen';
import DeleteAccountScreen from '@/screens/settings/DeleteAccountScreen';
import GuideScreen from '@/screens/guide/GuideScreen';
import RobotFaceScreen from '@/screens/robot/RobotFaceScreen';
import { userApi, UserInfo, childApi, ChildInfo, CHILD_PROFILE_IMAGE_CACHE_KEY } from '@/services/api';

type Screen =
  | 'splash'
  | 'login'
  | 'signup'
  | 'main'
  | 'conversation-detail'
  | 'daily-report'
  | 'video'
  | 'register-child'
  | 'calendar'
  | 'guide'
  | 'settings'
  | 'change-child-profile'
  | 'change-password'
  | 'logout-confirm'
  | 'delete-account'
  | 'robot-face';

const STORAGE_KEY_CURRENT_SCREEN = 'current_screen';

const VALID_SCREENS: Screen[] = [
  'splash',
  'login',
  'signup',
  'main',
  'conversation-detail',
  'daily-report',
  'video',
  'register-child',
  'calendar',
  'guide',
  'settings',
  'change-child-profile',
  'change-password',
  'logout-confirm',
  'delete-account',
  'robot-face',
];

const AUTH_REQUIRED_SCREENS: Screen[] = [
  'main',
  'conversation-detail',
  'daily-report',
  'video',
  'register-child',
  'calendar',
  'guide',
  'settings',
  'change-child-profile',
  'change-password',
  'logout-confirm',
  'delete-account',
  'robot-face',
];

const isScreen = (value: string | null): value is Screen =>
  value !== null && (VALID_SCREENS as string[]).includes(value);

const isAuthRequiredScreen = (screen: Screen) => AUTH_REQUIRED_SCREENS.includes(screen);

export default function Home() {
  const [currentScreen, setCurrentScreen] = useState<Screen>('splash');
  const [hasChild, setHasChild] = useState(false); // 아이 등록 여부
  const [userInfo, setUserInfo] = useState<UserInfo | null>(null); // 사용자 정보
  const [childInfo, setChildInfo] = useState<ChildInfo | null>(null); // 아이 정보
  const [childProfileImageUrl, setChildProfileImageUrl] = useState<string | null>(null);
  const profileImageObjectUrlRef = useRef<string | null>(null);
  const [isInitializing, setIsInitializing] = useState(true);
  const [authMessage, setAuthMessage] = useState<string | null>(null);

  // 초기 렌더 시 마지막 화면 복원
  useEffect(() => {
    if (typeof window === 'undefined') {
      return;
    }

    try {
      const savedRawScreen = localStorage.getItem(STORAGE_KEY_CURRENT_SCREEN);
      const savedScreen = isScreen(savedRawScreen) ? savedRawScreen : null;
      const token = localStorage.getItem('access_token');
      let nextScreen: Screen = 'splash';

      if (token) {
        if (savedScreen && isAuthRequiredScreen(savedScreen)) {
          nextScreen = savedScreen;
        } else {
          nextScreen = 'main';
        }
      } else if (savedScreen === 'login' || savedScreen === 'signup') {
        nextScreen = savedScreen;
      }

      setCurrentScreen(nextScreen);
    } catch (error) {
      console.error('화면 상태 복원 중 오류:', error);
      setCurrentScreen('splash');
    }

    setIsInitializing(false);
  }, []);

  // 화면 상태를 로컬 스토리지에 저장
  useEffect(() => {
    if (typeof window === 'undefined') {
      return;
    }

    if (isInitializing) {
      return;
    }

    try {
      localStorage.setItem(STORAGE_KEY_CURRENT_SCREEN, currentScreen);
    } catch (error) {
      console.error('화면 상태 저장 중 오류:', error);
    }
  }, [currentScreen, isInitializing]);

  const revokeProfileImageUrl = useCallback(() => {
    if (profileImageObjectUrlRef.current) {
      if (profileImageObjectUrlRef.current.startsWith('blob:')) {
        URL.revokeObjectURL(profileImageObjectUrlRef.current);
      }
      profileImageObjectUrlRef.current = null;
    }
    setChildProfileImageUrl(null);
  }, []);

  const refreshChildData = useCallback(async () => {
    const childPromise = childApi.getChild();
    const imagePromise = childApi.getChildProfileImage();

    const [childResult, imageResult] = await Promise.allSettled([childPromise, imagePromise]);

    const childResponse =
      childResult.status === 'fulfilled' ? childResult.value : { success: false as const, message: (childResult.reason as Error)?.message };

    if (childResponse.success && childResponse.data) {
      console.log('아이 정보 조회 성공:', childResponse.data);
      setChildInfo(childResponse.data);
      setHasChild(true);
    } else {
      console.log('아이 정보 조회 실패:', childResponse?.message);
      if (childResponse?.message?.includes('등록된 아이가 없습니다') || childResponse?.message?.includes('404')) {
        setHasChild(false);
        setChildInfo(null);
        revokeProfileImageUrl();
        return;
      }

      if (childResponse?.message?.includes('인증')) {
        localStorage.removeItem('access_token');
        setCurrentScreen('login');
        revokeProfileImageUrl();
      }
      return;
    }

    const imageResponse =
      imageResult.status === 'fulfilled' ? imageResult.value : { success: false as const, message: (imageResult.reason as Error)?.message };

    if (imageResponse.success && imageResponse.data) {
      if (profileImageObjectUrlRef.current && profileImageObjectUrlRef.current !== imageResponse.data) {
        if (profileImageObjectUrlRef.current.startsWith('blob:')) {
          URL.revokeObjectURL(profileImageObjectUrlRef.current);
        }
        profileImageObjectUrlRef.current = null;
      }

      if (imageResponse.data.startsWith('blob:')) {
        profileImageObjectUrlRef.current = imageResponse.data;
      } else {
        profileImageObjectUrlRef.current = null;
      }
      setChildProfileImageUrl(imageResponse.data);
    } else {
      revokeProfileImageUrl();
    }
  }, [revokeProfileImageUrl, setCurrentScreen]);

  const handleLogin = () => {
    console.log('로그인 버튼 클릭');
    setAuthMessage(null);
    setCurrentScreen('login');
  };

  const handleSignUp = () => {
    console.log('회원가입 버튼 클릭');
    setAuthMessage(null);
    setCurrentScreen('signup');
  };

  const handleBackToSplash = () => {
    setAuthMessage(null);
    setCurrentScreen('splash');
  };

  const handleLoginComplete = () => {
    console.log('로그인 완료');
    setAuthMessage(null);
    setCurrentScreen('main');
  };

  const handleSignUpComplete = () => {
    console.log('회원가입 완료');
    setAuthMessage('회원가입이 완료되었습니다. 로그인해주세요.');
    setCurrentScreen('login');
  };

  const handleLogout = () => {
    console.log('로그아웃');
    try {
      localStorage.removeItem('access_token');
      localStorage.removeItem(STORAGE_KEY_CURRENT_SCREEN);
      if (typeof sessionStorage !== 'undefined') {
        sessionStorage.removeItem(CHILD_PROFILE_IMAGE_CACHE_KEY);
      }
    } catch (error) {
      console.error('로그아웃 시 스토리지 정리 오류:', error);
    }
    setUserInfo(null);
    setChildInfo(null);
    setHasChild(false);
    setAuthMessage(null);
    revokeProfileImageUrl();
    setCurrentScreen('splash');
  };

  // 메인 페이지 진입 시 사용자 정보 및 아이 정보 조회
  useEffect(() => {
    if (isInitializing) {
      return;
    }

    const fetchData = async () => {
      if (currentScreen === 'main') {
        // 사용자 정보 조회
        const userResponse = await userApi.getMe();
        if (userResponse.success && userResponse.data) {
          console.log('사용자 정보 조회 성공:', userResponse.data);
          setUserInfo(userResponse.data);
        } else {
          console.error('사용자 정보 조회 실패:', userResponse.message);
          // 인증 오류인 경우 로그인 화면으로 이동
          if (userResponse.message?.includes('인증')) {
            localStorage.removeItem('access_token');
            setCurrentScreen('login');
            return;
          }
        }

        await refreshChildData();
      }
    };

    fetchData();
  }, [currentScreen, isInitializing, refreshChildData]);

  useEffect(() => {
    return () => {
      revokeProfileImageUrl();
    };
  }, [revokeProfileImageUrl]);

  if (isInitializing) {
    return null;
  }

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
    setCurrentScreen('guide');
  };

  const handleSettings = () => {
    console.log('설정 페이지로 이동');
    setCurrentScreen('settings');
  };

  const handleOpenRobotFace = () => {
    console.log('로봇 얼굴 페이지로 이동');
    setCurrentScreen('robot-face');
  };

  const handleCloseRobotFace = () => {
    console.log('로봇 얼굴 페이지 종료');
    setCurrentScreen('main');
  };

  const handleRegisterChild = () => {
    console.log('아이 등록 페이지로 이동');
    setCurrentScreen('register-child');
  };

  const handleRegisterChildComplete = () => {
    console.log('아이 등록 완료');
    setHasChild(true);
  refreshChildData();
    setCurrentScreen('main');
  };

  if (currentScreen === 'splash') {
    return <SplashScreen onLogin={handleLogin} onSignUp={handleSignUp} />;
  }

  if (currentScreen === 'login') {
    return (
      <LoginScreen
        onBack={handleBackToSplash}
        onLoginComplete={handleLoginComplete}
        onSignUp={handleSignUp}
        message={authMessage}
      />
    );
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
      childInfo={childInfo}
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

  if (currentScreen === 'guide') {
    return <GuideScreen 
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

  if (currentScreen === 'robot-face') {
    return <RobotFaceScreen onExit={handleCloseRobotFace} />;
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
        refreshChildData();
        setCurrentScreen('settings');
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
  onLogoClick={handleOpenRobotFace}
    hasChild={hasChild}
    childInfo={childInfo}
    childProfileImageUrl={childProfileImageUrl}
  />;
}
