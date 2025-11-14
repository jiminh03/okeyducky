import React, { useEffect, useMemo } from 'react';
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
};

const positions = {
  eyeLeft: { x: 430, y: 760 },
  eyeRight: { x: 1618, y: 760 },
  blushLeft: { x: 430, y: 1120 },
  blushRight: { x: 1618, y: 1120 },
  beak: { x: 1024, y: 1080 },
};

const RobotFaceScreen: React.FC<RobotFaceScreenProps> = ({ onExit }) => {
  useRobotFaceSocket({ head: true });

  const beakSrc = useMemo(() => encodeURI('/icons/오리 입.png'), []);

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
      <div className="robot-face-stage">
        <svg
          className="robot-face-svg"
          viewBox={`0 0 ${canvas.width} ${canvas.height}`}
          role="img"
          aria-hidden="true"
        >
          <rect width={canvas.width} height={canvas.height} fill="#ffffff" />

          <ellipse
            cx={positions.eyeLeft.x}
            cy={positions.eyeLeft.y}
            rx={features.eyeRadius}
            ry={features.eyeRadius}
            fill="#4d4d4d"
          />
          <circle
            cx={positions.eyeLeft.x + features.eyeRadius * 0.4}
            cy={positions.eyeLeft.y - features.eyeRadius * 0.4}
            r={features.eyeHighlightRadius}
            fill="#ffffff"
          />

          <ellipse
            cx={positions.eyeRight.x}
            cy={positions.eyeRight.y}
            rx={features.eyeRadius}
            ry={features.eyeRadius}
            fill="#4d4d4d"
          />
          <circle
            cx={positions.eyeRight.x + features.eyeRadius * 0.4}
            cy={positions.eyeRight.y - features.eyeRadius * 0.4}
            r={features.eyeHighlightRadius}
            fill="#ffffff"
          />

          <ellipse
            cx={positions.blushLeft.x}
            cy={positions.blushLeft.y}
            rx={features.blush.rx}
            ry={features.blush.ry}
            fill="rgba(255, 192, 203, 1)"
            opacity={features.blush.opacity}
          />
          <ellipse
            cx={positions.blushRight.x}
            cy={positions.blushRight.y}
            rx={features.blush.rx}
            ry={features.blush.ry}
            fill="rgba(255, 192, 203, 1)"
            opacity={features.blush.opacity}
          />

          <image
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
