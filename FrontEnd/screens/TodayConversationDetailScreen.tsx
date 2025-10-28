import React, { useState } from 'react';
import Footer from '@/components/Footer';
import './TodayConversationDetailScreen.css';

interface TodayConversationDetailScreenProps {
  onBack: () => void;
}

const TodayConversationDetailScreen: React.FC<TodayConversationDetailScreenProps> = ({ onBack }) => {
  const [isSummaryExpanded, setIsSummaryExpanded] = useState(true);

  return (
    <div className="conversation-detail-screen">
      {/* 상단 헤더 */}
      <div className="conversation-header">
        <div className="header-bottom">
          <button className="back-button" onClick={onBack}>
            <svg 
              width="36" 
              height="36" 
              viewBox="0 0 24 24" 
              fill="none" 
              xmlns="http://www.w3.org/2000/svg"
            >
              <path 
                d="M15 18L9 12L15 6" 
                stroke="currentColor" 
                strokeWidth="3" 
                strokeLinecap="round" 
                strokeLinejoin="round"
              />
            </svg>
          </button>
          <h1 className="page-title">오늘 대화</h1>
          <div className="header-spacer"></div>
        </div>
      </div>

      {/* 메인 콘텐츠 */}
      <div className="conversation-content-area">
        {/* 대화 요약 박스 */}
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
              <li>아이는 음악 시간에서 받은 긍정적인 피드백을 즐겁게 이야기함.</li>
              <li>친구들의 반응을 통해 성취감을 느끼고, 스스로 가수가 되고 싶다는 꿈을 표현함.</li>
              <li>전반적으로 밝고 신난 말투로 자신감을 보였으며, 상상 속 장면(무대, 가족 관람)을 구체적으로 묘사함.</li>
            </ul>
          )}
        </div>

        {/* 대화 내용 */}
        <div className="conversation-messages">
          {/* 시스템/부모 메시지 */}
          <div className="message-container system-message">
            <div className="message-bubble system-bubble">
              오늘 하루 어땠어? 재밌는 일 있었어?
            </div>
          </div>

          {/* 아이 응답 메시지 */}
          <div className="message-container child-message">
            <div className="message-bubble child-bubble">
              응! 오늘 음악 시간에 노래 불렀는데, 선생님이 목소리 예쁘대!
              <br />
              친구들도 박수 쳐줬어! 그래서 진짜 신났어! 그때 생각했어. 아, 나 진짜 노래가 좋구나!
              <br />
              그래서… 나 커서 가수가 될래! 무대에서 노래 부르고, 엄마 아빠랑 무키도 보러 오면 진짜 좋겠다!
            </div>
          </div>

          {/* 시스템/부모 메시지 (두 번째) */}
          <div className="message-container system-message">
            <div className="message-bubble system-bubble">
              오늘 하루 어땠어? 재밌는 일 있었어?
            </div>
          </div>
        </div>
      </div>

      {/* 하단 네비게이션 */}
      <Footer />
    </div>
  );
};

export default TodayConversationDetailScreen;

