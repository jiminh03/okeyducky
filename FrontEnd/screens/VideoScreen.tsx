import React, { useState } from 'react';
import Header from '@/components/Header';
import Footer from '@/components/Footer';
import './VideoScreen.css';

interface VideoScreenProps {
  onHome?: () => void;
  onVideo?: () => void;
  onCalendar?: () => void;
  onGuide?: () => void;
  onSettings?: () => void;
}

const VideoScreen: React.FC<VideoScreenProps> = ({ 
  onHome, 
  onVideo, 
  onCalendar, 
  onGuide, 
  onSettings 
}) => {
  const [message, setMessage] = useState('');

  const handleSend = () => {
    if (message.trim()) {
      console.log('메시지 전송:', message);
      setMessage('');
    }
  };

  return (
    <div className="video-screen">
      {/* 상단 헤더 */}
      <Header />

      {/* 메인 콘텐츠 */}
      <div className="video-content-area">
        {/* 비디오 목록 영역 */}
        <div className="video-list-container">
          {/* 비디오 목록이 여기에 표시됩니다 */}
        </div>
      </div>

      {/* 입력 바 */}
      <div className="video-input-bar">
          <input
            type="text"
            className="video-input"
            placeholder="아이에게 전하고 싶은 말을 입력하세요!"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyPress={(e) => {
              if (e.key === 'Enter') {
                handleSend();
              }
            }}
          />
          <button 
            className="video-send-button"
            onClick={handleSend}
            disabled={!message.trim()}
          >
            <svg 
              width="24" 
              height="24" 
              viewBox="0 0 24 24" 
              fill="none" 
              xmlns="http://www.w3.org/2000/svg"
            >
              <path 
                d="M22 2L11 13" 
                stroke="currentColor" 
                strokeWidth="2" 
                strokeLinecap="round" 
                strokeLinejoin="round"
              />
              <path 
                d="M22 2L15 22L11 13L2 9L22 2Z" 
                stroke="currentColor" 
                strokeWidth="2" 
                strokeLinecap="round" 
                strokeLinejoin="round"
              />
            </svg>
          </button>
      </div>

      {/* 하단 네비게이션 */}
      <Footer 
        activeTab="video"
        onHome={onHome}
        onVideo={onVideo}
        onCalendar={onCalendar}
        onGuide={onGuide}
        onSettings={onSettings}
      />
    </div>
  );
};

export default VideoScreen;

