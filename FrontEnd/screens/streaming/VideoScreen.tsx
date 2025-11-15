import React, { useState, useRef } from 'react';
import Header from '@/components/Header';
import Footer from '@/components/Footer';
import { ChildInfo, robotMessageApi } from '@/services/api';
import { useWebRTCViewer } from '@/services/webrtcViewer';
import './VideoScreen.css';

interface VideoScreenProps {
  onHome?: () => void;
  onVideo?: () => void;
  onCalendar?: () => void;
  onGuide?: () => void;
  onSettings?: () => void;
  childInfo?: ChildInfo | null;
}

const VideoScreen: React.FC<VideoScreenProps> = ({ 
  onHome, 
  onVideo, 
  onCalendar, 
  onGuide, 
  onSettings,
  childInfo,
}) => {
  const [message, setMessage] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [sendError, setSendError] = useState<string | null>(null);
  const remoteVideoRef = useRef<HTMLVideoElement>(null);
  const fallbackRobotIdEnv = process.env.NEXT_PUBLIC_TEST_ROBOT_ID;
  const parsedFallbackRobotId = fallbackRobotIdEnv ? Number(fallbackRobotIdEnv) : undefined;
  const hasFallbackRobot =
    typeof parsedFallbackRobotId === 'number' && !Number.isNaN(parsedFallbackRobotId);

  const {
    start: startStreaming,
    stop: stopStreaming,
    status,
    error,
    isStreaming,
    isConnecting,
    robotSource,
    hasRemoteStream,
  } = useWebRTCViewer({
    remoteVideoRef,
    childInfo,
    fallbackRobotId: hasFallbackRobot ? parsedFallbackRobotId : undefined,
  });

  const handleSend = async () => {
    const trimmedMessage = message.trim();
    if (!trimmedMessage || isSending) {
      return;
    }

    if (!childInfo?.child_id) {
      setSendError('아이 정보가 없습니다.');
      return;
    }

    setIsSending(true);
    setSendError(null);

    try {
      const result = await robotMessageApi.sendMessage(trimmedMessage, childInfo.child_id);
      
      if (result.success) {
        setMessage('');
        console.log('메시지 전송 성공:', trimmedMessage);
      } else {
        setSendError(result.message || '메시지 전송에 실패했습니다.');
        console.error('메시지 전송 실패:', result.message);
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : '메시지 전송 중 오류가 발생했습니다.';
      setSendError(errorMessage);
      console.error('메시지 전송 중 예외 발생:', error);
    } finally {
      setIsSending(false);
    }
  };

  const handleStartWebRTC = async () => {
    await startStreaming();
  };

  const handleStopWebRTC = () => {
    stopStreaming();
  };

  const getPrimaryMessage = () => {
    if (status === 'ended') {
      return '영상 통화가 종료되었습니다.';
    }

    if (isConnecting) {
      return '상대방과 연결 중입니다...';
    }

    if (!isStreaming && !isConnecting) {
      if (robotSource === 'fallback') {
        return '테스트용 로봇 ID로 연결 중입니다.';
      }
      return '화상 통화를 시작하면 연결된 로봇 화면이 표시됩니다.';
    }

    return '';
  };

  const primaryMessage = getPrimaryMessage();

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
                disabled={isConnecting}
              >
                <span className="webrtc-button-icon">📹</span>
                <span className="webrtc-button-text">
                  {isConnecting ? '연결 중...' : '화상 통화 시작'}
                </span>
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

          {/* 메시지 전송 에러 */}
          {sendError && (
            <div className="video-error-message">
              {sendError}
            </div>
          )}

          {primaryMessage && !error && !sendError && (
            <div className="video-info-message">
              {primaryMessage}
            </div>
          )}

          {/* WebRTC 비디오 스트림 (상대방 화면만 표시) - 버튼 누르면 회색 배경을 덮음 */}
          {(isStreaming || hasRemoteStream || isConnecting) && (
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
            disabled={!message.trim() || isSending}
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

