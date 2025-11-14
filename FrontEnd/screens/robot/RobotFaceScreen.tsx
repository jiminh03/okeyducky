import React, { useEffect, useMemo, useState } from 'react';
import { useRobotFaceSocket } from '@/services/robotFaceSocket';
import './RobotFaceScreen.css';

interface RobotFaceScreenProps {
  onExit?: () => void;
}

const canvas = {
  width: 2048,
  height: 1536,
};

const features = {
  eyeRadius: 210,
  eyeHighlightRadius: 48,
  blush: { rx: 210, ry: 76, opacity: 0.62 },
  beak: { width: 660, height: 360 },
  heartSize: 210, // 하트 크기
};

// 하트 모양 SVG path (중심 기준, 크기 조정 가능)
const getHeartPath = (size: number) => {
  const scale = size / 200;
  return `M 0,${-20 * scale} 
          C ${-50 * scale},${-70 * scale} ${-100 * scale},${-70 * scale} ${-100 * scale},${-20 * scale}
          C ${-100 * scale},${20 * scale} ${-50 * scale},${70 * scale} 0,${120 * scale}
          C ${50 * scale},${70 * scale} ${100 * scale},${20 * scale} ${100 * scale},${-20 * scale}
          C ${100 * scale},${-70 * scale} ${50 * scale},${-70 * scale} 0,${-20 * scale} Z`;
};

const positions = {
  eyeLeft: { x: 430, y: 760 },
  eyeRight: { x: 1618, y: 760 },
  blushLeft: { x: 430, y: 1120 },
  blushRight: { x: 1618, y: 1120 },
  beak: { x: 1024, y: 1080 },
};

const RobotFaceScreen: React.FC<RobotFaceScreenProps> = ({ onExit }) => {
  const { emotion } = useRobotFaceSocket({ head: true });
  const isHappy = emotion === 'happy';
  const heartPath = useMemo(() => getHeartPath(features.heartSize), []);
  const [isBlinking, setIsBlinking] = useState(false);
  const [eyeRy, setEyeRy] = useState(features.eyeRadius);
  const beakSrc = useMemo(() => encodeURI('/icons/오리 입.png'), []);

  // 눈 깜빡임 애니메이션 (happy일 때는 하트이므로 깜빡임 안 함)
  useEffect(() => {
    if (isHappy) {
      return; // happy일 때는 깜빡임 안 함
    }

    let blinkTimeout: NodeJS.Timeout;

    const scheduleBlink = () => {
      // 랜덤하게 2~5초마다 깜빡임
      const delay = Math.random() * 3000 + 2000;
      blinkTimeout = setTimeout(() => {
        setIsBlinking(true);
        setEyeRy(5); // 눈을 거의 닫음
        setTimeout(() => {
          setIsBlinking(false);
          setEyeRy(features.eyeRadius);
          // 깜빡임 후 다음 깜빡임 스케줄링
          scheduleBlink();
        }, 150); // 150ms 동안 닫힘
      }, delay);
    };

    scheduleBlink();

    return () => {
      if (blinkTimeout) {
        clearTimeout(blinkTimeout);
      }
    };
  }, [isHappy]);

  // emotion에 따른 눈 위치 조정
  const getEyeOffset = () => {
    switch (emotion) {
      case 'happy':
        return { y: -20 }; // 위로 올라감
      case 'sad':
        return { y: 20 }; // 아래로 내려감
      default:
        return { y: 0 };
    }
  };

  const eyeOffset = getEyeOffset();

  useEffect(() => {
    if (!onExit) {
      return undefined;
    }

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onExit();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onExit]);

  const handleDoubleClick = () => {
    onExit?.();
  };

  return (
    <div
      className="robot-face-fullscreen"
      onDoubleClick={handleDoubleClick}
      role={onExit ? 'button' : undefined}
      tabIndex={onExit ? 0 : undefined}
    >
      {onExit && (
        <button type="button" className="robot-face-back" onClick={onExit} aria-label="돌아가기">
          ←
        </button>
      )}
      <div className={`robot-face-stage emotion-${emotion}`}>
        <svg
          className="robot-face-svg"
          viewBox={`0 0 ${canvas.width} ${canvas.height}`}
          role="img"
          aria-hidden="true"
        >
          <rect width={canvas.width} height={canvas.height} fill="#ffffff" />

          {/* 왼쪽 눈 */}
          <g className="eye-group eye-left">
            {isHappy ? (
              <path
                className="eye eye-heart"
                d={heartPath}
                fill="#ff1744"
                transform={`translate(${positions.eyeLeft.x}, ${positions.eyeLeft.y + eyeOffset.y})`}
              />
            ) : (
              <>
                <ellipse
                  className="eye"
                  cx={positions.eyeLeft.x}
                  cy={positions.eyeLeft.y + eyeOffset.y}
                  rx={features.eyeRadius}
                  ry={eyeRy}
                  fill="#4d4d4d"
                />
                {!isBlinking && (
                  <circle
                    className="eye-highlight"
                    cx={positions.eyeLeft.x + features.eyeRadius * 0.4}
                    cy={positions.eyeLeft.y - features.eyeRadius * 0.4 + eyeOffset.y}
                    r={features.eyeHighlightRadius}
                    fill="#ffffff"
                  />
                )}
              </>
            )}
          </g>

          {/* 오른쪽 눈 */}
          <g className="eye-group eye-right">
            {isHappy ? (
              <path
                className="eye eye-heart"
                d={heartPath}
                fill="#ff1744"
                transform={`translate(${positions.eyeRight.x}, ${positions.eyeRight.y + eyeOffset.y})`}
              />
            ) : (
              <>
                <ellipse
                  className="eye"
                  cx={positions.eyeRight.x}
                  cy={positions.eyeRight.y + eyeOffset.y}
                  rx={features.eyeRadius}
                  ry={eyeRy}
                  fill="#4d4d4d"
                />
                {!isBlinking && (
                  <circle
                    className="eye-highlight"
                    cx={positions.eyeRight.x + features.eyeRadius * 0.4}
                    cy={positions.eyeRight.y - features.eyeRadius * 0.4 + eyeOffset.y}
                    r={features.eyeHighlightRadius}
                    fill="#ffffff"
                  />
                )}
              </>
            )}
          </g>

          <ellipse
            className="blush blush-left"
            cx={positions.blushLeft.x}
            cy={positions.blushLeft.y}
            rx={features.blush.rx}
            ry={features.blush.ry}
            fill="rgba(255, 192, 203, 1)"
            opacity={isHappy ? 0.8 : emotion === 'sad' ? 0.4 : features.blush.opacity}
          />
          <ellipse
            className="blush blush-right"
            cx={positions.blushRight.x}
            cy={positions.blushRight.y}
            rx={features.blush.rx}
            ry={features.blush.ry}
            fill="rgba(255, 192, 203, 1)"
            opacity={isHappy ? 0.8 : emotion === 'sad' ? 0.4 : features.blush.opacity}
          />

          <image
            className="beak"
            xlinkHref={beakSrc}
            href={beakSrc}
            x={positions.beak.x - features.beak.width / 2}
            y={positions.beak.y - features.beak.height / 2}
            width={features.beak.width}
            height={features.beak.height}
            preserveAspectRatio="xMidYMid meet"
          />
        </svg>
      </div>
    </div>
  );
};

export default RobotFaceScreen;
