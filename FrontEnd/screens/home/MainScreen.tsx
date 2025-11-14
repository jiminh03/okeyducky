import React, { useEffect, useState } from 'react';
import Header from '@/components/Header';
import Footer from '@/components/Footer';
import { ChildInfo, reportApi, DailyConversationLog, DailyAnalysisReport } from '@/services/api';
import './MainScreen.css';

interface MainScreenProps {
  onLogout: () => void;
  onConversationDetail?: () => void;
  onDailyReport?: () => void;
  onVideo?: () => void;
  onCalendar?: () => void;
  onGuide?: () => void;
  onSettings?: () => void;
  onRegisterChild?: () => void;
  onLogoClick?: () => void;
  hasChild?: boolean;
  childInfo?: ChildInfo | null;
  childProfileImageUrl?: string | null;
}

const MainScreen: React.FC<MainScreenProps> = ({ 
  onLogout, 
  onConversationDetail, 
  onDailyReport,
  onVideo,
  onCalendar,
  onGuide,
  onSettings,
  onRegisterChild,
  onLogoClick,
  hasChild = true,
  childInfo,
  childProfileImageUrl
}) => {
  const [todayLog, setTodayLog] = useState<DailyConversationLog | null>(null);
  const [todayReport, setTodayReport] = useState<DailyAnalysisReport | null>(null);
  const [isLoadingLog, setIsLoadingLog] = useState(false);
  const [isLoadingReport, setIsLoadingReport] = useState(false);

  // 오늘 날짜를 YYYY-MM-DD 형식으로 반환
  const getTodayDate = (): string => {
    const today = new Date();
    const year = today.getFullYear();
    const month = String(today.getMonth() + 1).padStart(2, '0');
    const day = String(today.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  };

  // 일일 대화 로그 조회
  useEffect(() => {
    if (hasChild) {
      const fetchTodayLog = async () => {
        setIsLoadingLog(true);
        const today = getTodayDate();
        const response = await reportApi.getDailyLog(today);
        
        if (response.success && response.data) {
          setTodayLog(response.data);
        } else {
          // 404인 경우는 정상 (아직 대화가 없을 수 있음)
          if (!response.message?.includes('404')) {
            console.error('일일 대화 로그 조회 실패:', response.message);
          }
        }
        setIsLoadingLog(false);
      };

      fetchTodayLog();
    }
  }, [hasChild]);

  // 일일 AI 분석 리포트 조회
  useEffect(() => {
    if (hasChild) {
      const fetchTodayReport = async () => {
        setIsLoadingReport(true);
        const today = getTodayDate();
        const response = await reportApi.getDailyAnalysis(today);
        
        if (response.success && response.data) {
          setTodayReport(response.data);
        } else {
          // 404인 경우는 정상 (아직 리포트가 없을 수 있음)
          if (!response.message?.includes('404')) {
            console.error('일일 AI 분석 리포트 조회 실패:', response.message);
          }
        }
        setIsLoadingReport(false);
      };

      fetchTodayReport();
    }
  }, [hasChild]);

  // 날짜를 한국어 형식으로 변환 (예: 10월 18일)
  const formatDateKorean = (dateStr: string): string => {
    if (!dateStr) return '';
    try {
      const [year, month, day] = dateStr.split('-');
      const monthNum = parseInt(month, 10);
      const dayNum = parseInt(day, 10);
      return `${monthNum}월 ${dayNum}일`;
    } catch {
      return dateStr;
    }
  };

  const formatBirthDate = (dateStr: string): string => {
    if (!dateStr) return '';
    try {
      const [year, month, day] = dateStr.split('-');
      return `${year}. ${month}. ${day}.`;
    } catch {
      return dateStr;
    }
  };

  const getGenderSymbol = (gender?: ChildInfo['gender']): string => {
    if (gender === 'female') return '♀';
    if (gender === 'male') return '♂';
    return '⚪';
  };

  // daily_summary를 리스트로 변환 (줄바꿈 기준)
  const parseSummaryToList = (summary: string): string[] => {
    if (!summary) return [];
    return summary.split('\n').filter(line => line.trim().length > 0);
  };

  return (
    <div className="main-screen">
      {/* 상단 헤더 */}
      <Header onLogoClick={onLogoClick} />

      {/* 메인 콘텐츠 */}
      <div className={`main-content-area ${!hasChild ? 'no-scroll' : ''}`}>
        {!hasChild ? (
          /* 아이 미등록 상태 */
          <div className="empty-state-container">
            <div 
              className="register-card"
              onClick={onRegisterChild}
              style={{ cursor: onRegisterChild ? 'pointer' : 'default' }}
            >
              <div className="plus-icon">+</div>
              <div className="register-text">아이를 등록해주세요</div>
            </div>
          </div>
        ) : (
          /* 아이 등록 상태 */
          <>
            {/* 프로필 카드 */}
            <div className="profile-card">
            <div className="profile-image">
              {childProfileImageUrl ? (
                <img
                  src={childProfileImageUrl}
                  alt={`${childInfo?.name ?? ''} 프로필 이미지`}
                  className="profile-photo"
                />
              ) : childInfo?.profile_img_url ? (
                <img
                  src={childInfo.profile_img_url}
                  alt={`${childInfo.name} 프로필 이미지`}
                  className="profile-photo"
                />
              ) : (
                <div className="avatar-placeholder">
                  {childInfo?.gender === 'female' ? '👧' : '👦'}
                </div>
              )}
            </div>
              <div className="profile-info">
                <div className="profile-name">
                  <span className="name">{childInfo?.name || '이름 없음'}</span>
                  <span className={`gender ${childInfo?.gender === 'male' ? 'male' : 'female'}`}>
                    {childInfo ? getGenderSymbol(childInfo.gender) : '♀'}
                  </span>
                </div>
                <div className="profile-detail">
                  {childInfo ? formatBirthDate(childInfo.birth_date) : '2017. 03. 13.'}
                </div>
                <div className="profile-detail">
                  {childInfo?.school || '명덕초등학교 2학년'}
                </div>
              </div>
            </div>

            {/* 카드 컨테이너 */}
            <div className="cards-container">
              {/* 오늘 대화 카드 */}
              <div className="content-card today-conversation-card">
                <div className="card-header">
                  <h3 className="card-title">오늘 대화</h3>
                  <span 
                    className="card-link" 
                    onClick={onConversationDetail}
                    style={{ cursor: 'pointer' }}
                  >
                    자세히 보기 {'>'}
                  </span>
                </div>
                <div className="card-content">
                  <div className="highlight-text">대화 요약</div>
                  {isLoadingLog ? (
                    <div style={{ color: '#999', fontSize: '14px', padding: '10px 0' }}>로딩 중...</div>
                  ) : todayLog?.daily_summary ? (
                    <ul className="conversation-list">
                      {parseSummaryToList(todayLog.daily_summary).map((item, index) => (
                        <li key={index}>{item}</li>
                      ))}
                    </ul>
                  ) : (
                    <div style={{ color: '#999', fontSize: '14px', padding: '10px 0' }}>
                      오늘 대화가 아직 없습니다.
                    </div>
                  )}
                </div>
              </div>

              {/* 일일 리포트 카드 */}
              <div className="content-card report-card">
                <div className="card-header">
                  <h3 className="card-title">일일 리포트</h3>
                  <span 
                    className="card-link" 
                    onClick={onDailyReport}
                    style={{ cursor: 'pointer' }}
                  >
                    자세히 보기 {'>'}
                  </span>
                </div>
                <div className="card-content">
                  {isLoadingReport ? (
                    <div style={{ color: '#999', fontSize: '14px', padding: '10px 0' }}>로딩 중...</div>
                  ) : todayReport ? (
                    <>
                      <div className="report-date">
                        📅 {formatDateKorean(todayReport.date)} 일일 리포트
                      </div>
                      <div className="report-summary">
                        {todayReport.analysis_summary || '리포트 내용이 없습니다.'}
                      </div>
                    </>
                  ) : (
                    <div style={{ color: '#999', fontSize: '14px', padding: '10px 0' }}>
                      오늘 리포트가 아직 없습니다.
                    </div>
                  )}
                </div>
              </div>
            </div>
          </>
        )}
      </div>

      {/* 하단 네비게이션 */}
      <Footer 
        activeTab="home"
        onVideo={onVideo}
        onCalendar={onCalendar}
        onGuide={onGuide}
        onSettings={onSettings}
      />
    </div>
  );
};

export default MainScreen;

