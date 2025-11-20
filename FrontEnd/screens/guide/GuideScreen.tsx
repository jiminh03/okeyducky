import React from 'react';
import Header from '@/components/Header';
import Footer from '@/components/Footer';
import './GuideScreen.css';

interface GuideScreenProps {
  onHome?: () => void;
  onVideo?: () => void;
  onCalendar?: () => void;
  onGuide?: () => void;
  onSettings?: () => void;
}

const GuideScreen: React.FC<GuideScreenProps> = ({
  onHome,
  onVideo,
  onCalendar,
  onGuide,
  onSettings
}) => {
  return (
    <div className="guide-screen">
      {/* 상단 헤더 */}
      <Header />

      {/* 메인 콘텐츠 */}
      <div className="guide-content-area">
        <div className="guide-container">
          {/* 메인 제목 */}
          <h1 className="guide-main-title">
            👨‍👩‍👧 9살 아이 부모를 위한 육아 가이드
          </h1>

          {/* 부제목 */}
          <p className="guide-subtitle">
            아이의 마음을 듣고, 스스로 성장할 수 있게 돕는 공감 중심 양육법
          </p>

          {/* 가이드 섹션들 */}
          <div className="guide-sections">
            {/* 정서 발달 */}
            <div className="guide-section">
              <h2 className="guide-section-title">🧠 정서 발달</h2>
              <ul className="guide-section-list">
                <li>"괜찮아?"보다 "속상했겠다"로 공감 전달</li>
                <li>해결보다 경청이 우선 — 스스로 감정을 정리할 기회 제공</li>
              </ul>
            </div>

            {/* 또래 관계 */}
            <div className="guide-section">
              <h2 className="guide-section-title">👭 또래 관계</h2>
              <ul className="guide-section-list">
                <li>친구와의 갈등은 감정 중심으로 질문</li>
                <li>"그땐 어떤 기분이었어?"로 스스로 돌이켜보게 유도</li>
              </ul>
            </div>

            {/* 자기 효능감 */}
            <div className="guide-section">
              <h2 className="guide-section-title">💪 자기 효능감</h2>
              <ul className="guide-section-list">
                <li>어려운 일은 작은 단계로 나누기</li>
                <li>결과보다 노력 중심 칭찬 → 자존감 강화</li>
              </ul>
            </div>

            {/* 대화 습관 */}
            <div className="guide-section">
              <h2 className="guide-section-title">💬 대화 습관</h2>
              <ul className="guide-section-list">
                <li>즉각 반응보다 2~3초 기다리기</li>
                <li>부모가 하루를 먼저 공유하면 아이도 자연스레 이야기 시작</li>
              </ul>
            </div>

            {/* 기기 사용 */}
            <div className="guide-section">
              <h2 className="guide-section-title">📱 기기 사용</h2>
              <ul className="guide-section-list">
                <li>일방적 통제 X → 함께 약속 정하기</li>
                <li>"30분만 봐야 해"보다 "시간 정해야 다른 것도 할 수 있지?"</li>
              </ul>
            </div>

            {/* 유대 강화 */}
            <div className="guide-section">
              <h2 className="guide-section-title">💞 유대 강화</h2>
              <ul className="guide-section-list">
                <li>아이가 한 말을 기억해 다시 언급하기</li>
                <li>매일 5분 '질문 없는 대화 시간'으로 안정감 형성</li>
              </ul>
            </div>

            {/* 오리 로봇 활용 팁 */}
            <div className="guide-section">
              <h2 className="guide-section-title">🦆 오리 로봇 활용 팁</h2>
              <ul className="guide-section-list">
                <li>아이의 감정 표현을 자연스럽게 유도하고,</li>
                <li>부모는 리포트를 통해 즉각 공감 피드백 전달</li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      {/* 하단 네비게이션 */}
      <Footer 
        activeTab="guide"
        onHome={onHome}
        onVideo={onVideo}
        onCalendar={onCalendar}
        onGuide={onGuide}
        onSettings={onSettings}
      />
    </div>
  );
};

export default GuideScreen;

