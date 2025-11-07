import React, { useState, useRef, useEffect } from 'react';
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
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string>('');
  
  // WebRTC 관련 refs (백엔드 코드에서 사용할 수 있도록 준비)
  const remoteVideoRef = useRef<HTMLVideoElement>(null);

  // 컴포넌트 언마운트 시 정리
  useEffect(() => {
    return () => {
      // 컴포넌트 언마운트 시 WebRTC 연결 정리
      if (isStreaming) {
        handleStopWebRTC();
      }
    };
  }, [isStreaming]);

  const handleSend = () => {
    if (message.trim()) {
      console.log('메시지 전송:', message);
      setMessage('');
    }
  };

  const handleStartWebRTC = async () => {
    try {
      setError('');
      console.log('WebRTC 스트리밍 시작');
      setIsStreaming(true);

      // TODO: 백엔드에서 제공할 WebRTC 코드를 여기에 통합
      // 예시:
      // const webrtcConfig = await getWebRTCConfig(); // 백엔드 API로 설정 가져오기
      // await startWebRTCConnection(webrtcConfig, remoteVideoRef);
      
      // 백엔드 코드에서는 remoteVideoRef.current를 사용하여 비디오 스트림을 표시할 수 있습니다
      
    } catch (err) {
      console.error('WebRTC 시작 오류:', err);
      setError(err instanceof Error ? err.message : 'WebRTC 연결에 실패했습니다.');
      setIsStreaming(false);
    }
  };

  const handleStopWebRTC = () => {
    console.log('WebRTC 스트리밍 중지');

    // TODO: 백엔드에서 제공할 WebRTC 종료 코드를 여기에 통합
    // 예시:
    // stopWebRTCConnection();

    // 임시 정리
    if (remoteVideoRef.current) {
      remoteVideoRef.current.srcObject = null;
    }

    setIsStreaming(false);
    setError('');
  };

  return (
    <div className="video-screen">
      {/* 상단 헤더 */}
      <Header />

      {/* 메인 콘텐츠 */}
      <div className="video-content-area">
        {/* 비디오 목록 영역 */}
        <div className="video-list-container">
          {/* WebRTC 스트리밍 버튼 */}
          <div className="webrtc-control-container">
            {!isStreaming ? (
              <button 
                className="webrtc-start-button"
                onClick={handleStartWebRTC}
              >
                <span className="webrtc-button-icon">📹</span>
                <span className="webrtc-button-text">화상 통화 시작</span>
              </button>
            ) : (
              <button 
                className="webrtc-stop-button"
                onClick={handleStopWebRTC}
              >
                <span className="webrtc-button-icon">⏹</span>
                <span className="webrtc-button-text">화상 통화 중지</span>
              </button>
            )}
          </div>

          {/* 에러 메시지 */}
          {error && (
            <div className="video-error-message">
              {error}
            </div>
          )}

          {/* WebRTC 비디오 스트림 (상대방 화면만 표시) - 버튼 누르면 회색 배경을 덮음 */}
          {isStreaming && (
            <video
              ref={remoteVideoRef}
              autoPlay
              playsInline
              className="remote-video-fullscreen"
            />
          )}

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

