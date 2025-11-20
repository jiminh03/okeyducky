import React, { useState, useEffect } from 'react';
import Footer from '@/components/Footer';
import DetailHeader from '@/components/DetailHeader';
import { reportApi, DailyConversationLog } from '@/services/api';
import './TodayConversationDetailScreen.css';

interface TodayConversationDetailScreenProps {
  onBack: () => void;
  onHome?: () => void;
  onVideo?: () => void;
  onCalendar?: () => void;
  onGuide?: () => void;
  onSettings?: () => void;
}

const TodayConversationDetailScreen: React.FC<TodayConversationDetailScreenProps> = ({ 
  onBack,
  onHome,
  onVideo,
  onCalendar,
  onGuide,
  onSettings
}) => {
  const [isSummaryExpanded, setIsSummaryExpanded] = useState(true);
  const [todayLog, setTodayLog] = useState<DailyConversationLog | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string>('');

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
    const fetchTodayLog = async () => {
      setIsLoading(true);
      const today = getTodayDate();
      const response = await reportApi.getDailyLog(today);
      
      if (response.success && response.data) {
        setTodayLog(response.data);
      } else {
        if (response.message?.includes('404')) {
          setErrorMessage('오늘 대화가 아직 없습니다.');
        } else {
          setErrorMessage(response.message || '대화 로그를 불러오는데 실패했습니다.');
        }
      }
      setIsLoading(false);
    };

    fetchTodayLog();
  }, []);

  // daily_summary를 리스트로 변환 (줄바꿈 기준)
  const parseSummaryToList = (summary: string): string[] => {
    if (!summary) return [];
    return summary.split('\n').filter(line => line.trim().length > 0);
  };

  // 타임스탬프를 시간 형식으로 변환
  const formatTime = (timestamp: string): string => {
    try {
      const date = new Date(timestamp);
      const hours = String(date.getHours()).padStart(2, '0');
      const minutes = String(date.getMinutes()).padStart(2, '0');
      return `${hours}:${minutes}`;
    } catch {
      return '';
    }
  };

  return (
    <div className="conversation-detail-screen">
      {/* 상단 헤더 */}
      <DetailHeader title="오늘 대화" onBack={onBack} />

      {/* 메인 콘텐츠 */}
      <div className="conversation-content-area">
        {isLoading ? (
          <div style={{ textAlign: 'center', padding: '40px' }}>
            <div>로딩 중...</div>
          </div>
        ) : errorMessage ? (
          <div style={{ textAlign: 'center', padding: '40px', color: '#999' }}>
            <div>{errorMessage}</div>
          </div>
        ) : (
          <>
            {/* 대화 요약 박스 */}
            {todayLog?.daily_summary && (
              <div className="summary-box">
                <div className="summary-header">
                  <h2 className="summary-title">대화 요약</h2>
                  <button 
                    className={`expand-button ${isSummaryExpanded ? 'expanded' : 'collapsed'}`}
                    onClick={() => setIsSummaryExpanded(!isSummaryExpanded)}
                  >
                    <svg 
                      width="24" 
                      height="24" 
                      viewBox="0 0 24 24" 
                      fill="none" 
                      xmlns="http://www.w3.org/2000/svg"
                    >
                      <path 
                        d="M9 18L15 12L9 6" 
                        stroke="currentColor" 
                        strokeWidth="3" 
                        strokeLinecap="round" 
                        strokeLinejoin="round"
                      />
                    </svg>
                  </button>
                </div>
                {isSummaryExpanded && (
                  <ul className="summary-list">
                    {parseSummaryToList(todayLog.daily_summary).map((item, index) => (
                      <li key={index}>{item}</li>
                    ))}
                  </ul>
                )}
              </div>
            )}

            {/* 대화 내용 */}
            {todayLog?.logs && todayLog.logs.length > 0 ? (
              <div className="conversation-messages">
                {todayLog.logs.map((log, index) => (
                  <div 
                    key={index} 
                    className={`message-container ${
                      log.speaker === 'child' ? 'child-message' : 'system-message'
                    }`}
                  >
                    <div className={`message-bubble ${
                      log.speaker === 'child' ? 'child-bubble' : 'system-bubble'
                    }`}>
                      <div style={{ marginBottom: '4px', fontSize: '12px', color: '#999' }}>
                        {formatTime(log.timestamp)}
                      </div>
                      {log.message.split('\n').map((line, lineIndex) => (
                        <React.Fragment key={lineIndex}>
                          {line}
                          {lineIndex < log.message.split('\n').length - 1 && <br />}
                        </React.Fragment>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div style={{ textAlign: 'center', padding: '40px', color: '#999' }}>
                대화 내역이 없습니다.
              </div>
            )}
          </>
        )}
      </div>

      {/* 하단 네비게이션 */}
      <Footer 
        activeTab="home"
        onHome={onHome}
        onVideo={onVideo}
        onCalendar={onCalendar}
        onGuide={onGuide}
        onSettings={onSettings}
      />
    </div>
  );
};

export default TodayConversationDetailScreen;

