import React, { useState, useEffect } from 'react';
import Footer from '@/components/Footer';
import DetailHeader from '@/components/DetailHeader';
import { reportApi, DailyAnalysisReport } from '@/services/api';
import './DailyReportScreen.css';

interface DailyReportScreenProps {
  onBack: () => void;
  onHome?: () => void;
  onVideo?: () => void;
  onCalendar?: () => void;
  onGuide?: () => void;
  onSettings?: () => void;
}

const DailyReportScreen: React.FC<DailyReportScreenProps> = ({ 
  onBack,
  onHome,
  onVideo,
  onCalendar,
  onGuide,
  onSettings
}) => {
  const [todayReport, setTodayReport] = useState<DailyAnalysisReport | null>(null);
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

  // 일일 AI 분석 리포트 조회
  useEffect(() => {
    const fetchTodayReport = async () => {
      setIsLoading(true);
      const today = getTodayDate();
      const response = await reportApi.getDailyAnalysis(today);
      
      if (response.success && response.data) {
        setTodayReport(response.data);
      } else {
        if (response.message?.includes('404')) {
          setErrorMessage('오늘 리포트가 아직 없습니다.');
        } else {
          setErrorMessage(response.message || '리포트를 불러오는데 실패했습니다.');
        }
      }
      setIsLoading(false);
    };

    fetchTodayReport();
  }, []);

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

  return (
    <div className="daily-report-screen">
      {/* 상단 헤더 */}
      <DetailHeader title="일일 리포트" onBack={onBack} />

      {/* 메인 콘텐츠 */}
      <div className="report-content-area">
        {isLoading ? (
          <div style={{ textAlign: 'center', padding: '40px' }}>
            <div>로딩 중...</div>
          </div>
        ) : errorMessage ? (
          <div style={{ textAlign: 'center', padding: '40px', color: '#999' }}>
            <div>{errorMessage}</div>
          </div>
        ) : todayReport ? (
          <div className="daily-report-detail-card">
            {/* 리포트 헤더 */}
            <div className="daily-report-card-header">
              <div className="report-date">
                <span className="calendar-icon">📅</span>
                <span>{formatDateKorean(todayReport.date)} 리포트</span>
              </div>
            </div>

            {/* AI 분석 요약 섹션 */}
            <div className="report-section">
              <h3 className="report-section-title">AI 분석 요약</h3>
              <p className="report-section-content">
                {todayReport.analysis_summary || '분석 내용이 없습니다.'}
              </p>
            </div>
          </div>
        ) : (
          <div style={{ textAlign: 'center', padding: '40px', color: '#999' }}>
            리포트 데이터가 없습니다.
          </div>
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

export default DailyReportScreen;

