import React from 'react';
import Footer from '@/components/Footer';
import DetailHeader from '@/components/DetailHeader';
import './DailyReportScreen.css';

interface DailyReportScreenProps {
  onBack: () => void;
}

const DailyReportScreen: React.FC<DailyReportScreenProps> = ({ onBack }) => {
  return (
    <div className="daily-report-screen">
      {/* 상단 헤더 */}
      <DetailHeader title="일일 리포트" onBack={onBack} />

      {/* 메인 콘텐츠 */}
      <div className="report-content-area">
        {/* 리포트 카드 */}
        <div className="daily-report-detail-card">
          {/* 리포트 헤더 */}
          <div className="daily-report-card-header">
            <div className="report-date">
              <span className="calendar-icon">📅</span>
              <span>10월 18일 리포트</span>
            </div>
            <div className="report-time">시간: 18:10</div>
          </div>

          {/* 상황 섹션 */}
          <div className="report-section">
            <h3 className="report-section-title">상황</h3>
            <p className="report-section-content">
              부모가 앱을 통해 질문 전송 → 오리가 음성으로 전달
            </p>
          </div>

          {/* 대화 요약 섹션 */}
          <div className="report-section">
            <h3 className="report-section-title">대화 요약</h3>
            <ul className="report-summary-list">
              <li>아이는 음악 시간에서 받은 긍정적인 피드백을 즐겁게 이야기함.</li>
              <li>친구들의 반응을 통해 성취감을 느끼고, 스스로 '가수가 되고 싶다'는 꿈을 표현함.</li>
              <li>전반적으로 밝고 신난 말투로 자신감을 보였으며, 상상 속 장면(무대, 가족 관람)을 구체적으로 묘사함.</li>
            </ul>
          </div>

          {/* 주요 발화 섹션 */}
          <div className="report-section">
            <h3 className="report-section-title">주요 발화</h3>
            <div className="report-utterances">
              <div className="utterance-item">
                "오늘 음악 시간에 노래 불렀는데, 선생님이 목소리 예쁘대!"
              </div>
              <div className="utterance-item">
                "그래서… 나 커서 가수가 될래! 무대에서 노래 부르고, 엄마 아빠랑 무키도 보러 오면 진짜 좋겠다!"
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 하단 네비게이션 */}
      <Footer />
    </div>
  );
};

export default DailyReportScreen;

