import React from 'react';
import Header from '@/components/Header';
import './MainScreen.css';

interface MainScreenProps {
  onLogout: () => void;
}

const MainScreen: React.FC<MainScreenProps> = ({ onLogout }) => {
  return (
    <div className="main-screen">
      {/* 상단 헤더 */}
      <Header />

      {/* 메인 콘텐츠 */}
      <div className="main-content-area">
        {/* 프로필 카드 */}
        <div className="profile-card">
          <div className="profile-image">
            <div className="avatar-placeholder">👧</div>
          </div>
          <div className="profile-info">
            <div className="profile-name">
              <span className="name">이원희</span>
              <span className="gender">♀</span>
            </div>
            <div className="profile-detail">2017. 03. 13.</div>
            <div className="profile-detail">명덕초등학교 2학년</div>
          </div>
        </div>

        {/* 오늘 대화 카드 */}
        <div className="content-card today-conversation-card">
          <div className="card-header">
            <h3 className="card-title">오늘 대화</h3>
            <span className="card-link">자세히 보기 {'>'}</span>
          </div>
          <div className="card-content">
            <div className="highlight-text">대화 요약</div>
            <ul className="conversation-list">
              <li>아이는 음악 시간에서 받은 긍정적인 피드백을 즐겁게 이야기함.</li>
              <li>친구들의 반응을 통해 성취감을 느끼고, 스스로 '가수가 되고 싶다'는 꿈을 표현함.</li>
              <li>전반적으로 밝고 신난 말투로 자신감을 보였으며, 상상 속 장면(무대, 가족 관람)을 구체적으로 묘사함.</li>
            </ul>
          </div>
        </div>

        {/* 일일 리포트 카드 */}
        <div className="content-card report-card">
          <div className="card-header">
            <h3 className="card-title">일일 리포트</h3>
            <span className="card-link">자세히 보기 {'>'}</span>
          </div>
          <div className="card-content">
            <div className="report-date">📅 10월 18일 일일 리포트</div>
            <div className="report-summary">
              요약: 음악 시간의 긍정적 경험을 통해 자신감을 얻고, 미래에 대한 구체적인 꿈(가수가 되는 것)을 표현하며, 
              친구들과의 관계에서도 긍정적인 상호작용을 보임.
            </div>
          </div>
        </div>
      </div>

      {/* 하단 네비게이션 */}
      <div className="bottom-nav">
        <div className="nav-item active">
          <span className="nav-icon">🏠</span>
          <span className="nav-label">홈</span>
        </div>
        <div className="nav-item">
          <span className="nav-icon">🎥</span>
          <span className="nav-label">영상</span>
        </div>
        <div className="nav-item">
          <span className="nav-icon">📅</span>
          <span className="nav-label">달력</span>
        </div>
        <div className="nav-item">
          <span className="nav-icon">📖</span>
          <span className="nav-label">가이드</span>
        </div>
        <div className="nav-item">
          <span className="nav-icon">⚙️</span>
          <span className="nav-label">설정</span>
        </div>
      </div>
    </div>
  );
};

export default MainScreen;

