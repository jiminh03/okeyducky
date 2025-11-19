import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { io, Socket } from 'socket.io-client';

const DEFAULT_SOCKET_URL = process.env.NEXT_PUBLIC_ROBOT_FACE_SOCKET_URL || 'https://k13a408.p.ssafy.io';
const DEFAULT_SOCKET_PATH = process.env.NEXT_PUBLIC_ROBOT_FACE_SOCKET_PATH || '/socket.io';
const DEFAULT_REGISTER_EVENT = process.env.NEXT_PUBLIC_ROBOT_FACE_REGISTER_EVENT || 'robot-face:register';

const ConnectEvents = {
  AUTH_SUCCESS: 'auth_success',
  AUTH_FAILURE: 'auth_failure',
} as const;

// 백엔드 FaceEvent Enum에 대응하는 이벤트 이름
export enum FaceEvent {
  FACE_NORMAL = 'server:face_normal',
  FACE_HEART = 'server:face_heart',
  FACE_SAD = 'server:face_sad',
  FACE_SPEAKING = 'server:face_speaking',
  FACE_NOT_SPEAKING = 'server:face_not_speaking',
}

export type RobotEmotion = 'neutral' | 'happy' | 'sad';

export interface RobotFacePayload {
  type?: string;
  emotion?: RobotEmotion;
  message?: string;
  confidence?: number;
  speaking?: boolean; // 말하는 상태 여부
  [key: string]: unknown;
}

export type RobotFaceSocketStatus = 'idle' | 'connecting' | 'open' | 'closed' | 'error';

interface UseRobotFaceSocketOptions {
  head?: boolean;
  enabled?: boolean;
  autoReconnect?: boolean;
  reconnectDelayMs?: number;
}

interface UseRobotFaceSocketResult {
  status: RobotFaceSocketStatus;
  emotion: RobotEmotion; // 눈 상태 (neutral, happy, sad)
  speaking: boolean; // 입 상태 (말하는/말하지 않는)
  lastPayload: RobotFacePayload | null;
  lastUpdated: number | null;
  error: string | null;
  connect: () => void;
  disconnect: () => void;
}

const isBrowser = typeof window !== 'undefined';

const defaultOptions: Required<Omit<UseRobotFaceSocketOptions, 'enabled'>> & { enabled: boolean } = {
  head: true,
  enabled: true,
  autoReconnect: true,
  reconnectDelayMs: 5000,
};

export const useRobotFaceSocket = (options?: UseRobotFaceSocketOptions): UseRobotFaceSocketResult => {
  const { head, enabled, autoReconnect, reconnectDelayMs } = useMemo(
    () => ({ ...defaultOptions, ...(options ?? {}) }),
    [options]
  );

  const [status, setStatus] = useState<RobotFaceSocketStatus>('idle');
  const [emotion, setEmotion] = useState<RobotEmotion>('neutral');
  const [speaking, setSpeaking] = useState<boolean>(false);
  const [lastPayload, setLastPayload] = useState<RobotFacePayload | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<number | null>(null);
  const socketRef = useRef<Socket | null>(null);

  const registerHandlers = useCallback(
    (socket: Socket) => {
      socket.on('connect', () => {
        console.log('✅ [로봇 표정 소켓] 연결 성공');
        setStatus('open');
        setError(null);
      });

      socket.on(ConnectEvents.AUTH_SUCCESS, () => {
        console.log('🔑 [로봇 표정 소켓] 인증 성공');
        socket.emit(DEFAULT_REGISTER_EVENT, { head });
      });

      socket.on(ConnectEvents.AUTH_FAILURE, (message) => {
        const errorMsg = typeof message === 'string' ? message : '인증에 실패했습니다. 다시 로그인해주세요.';
        console.error('❌ [로봇 표정 소켓] 인증 실패:', errorMsg);
        setError(errorMsg);
        setStatus('error');
      });

      socket.on('disconnect', () => {
        console.log('🔌 [로봇 표정 소켓] 연결 종료');
        setStatus('closed');
      });

      socket.on('connect_error', err => {
        const errorInfo = err as { message?: string; description?: unknown; data?: unknown; type?: string };
        const errorMessage = errorInfo?.message || err?.toString() || '알 수 없는 오류';
        console.error('❌ [로봇 표정 소켓] 연결 오류:', {
          message: errorMessage,
          error: err,
          type: errorInfo?.type,
          description: errorInfo?.description,
          data: errorInfo?.data,
        });
        setError(`웹소켓 연결 실패: ${errorMessage}`);
        setStatus('error');
      });

      // 백엔드 FaceEvent 이벤트들 리스닝
      // 평소, 하트눈, 슬픈 얼굴: 눈만 변경
      socket.on(FaceEvent.FACE_NORMAL, () => {
        console.log('😐 [로봇 표정] 평소 얼굴 (눈만 변경)');
        setEmotion('neutral');
        // 입 상태는 변경하지 않음
        setLastPayload({ emotion: 'neutral' });
        setLastUpdated(Date.now());
      });

      socket.on(FaceEvent.FACE_HEART, () => {
        console.log('❤️ [로봇 표정] 하트눈 얼굴 (눈만 변경)');
        setEmotion('happy');
        // 입 상태는 변경하지 않음
        setLastPayload({ emotion: 'happy' });
        setLastUpdated(Date.now());
      });

      socket.on(FaceEvent.FACE_SAD, () => {
        console.log('😢 [로봇 표정] 슬픈 얼굴 (눈만 변경)');
        setEmotion('sad');
        // 입 상태는 변경하지 않음
        setLastPayload({ emotion: 'sad' });
        setLastUpdated(Date.now());
      });

      // 말하는 얼굴, 말하지 않는 얼굴: 입만 변경
      socket.on(FaceEvent.FACE_SPEAKING, () => {
        console.log('🗣️ [로봇 표정] 말하는 얼굴 (입만 변경)');
        setSpeaking(true);
        // 눈 상태는 변경하지 않음
        setLastPayload({ speaking: true });
        setLastUpdated(Date.now());
      });

      socket.on(FaceEvent.FACE_NOT_SPEAKING, () => {
        console.log('😐 [로봇 표정] 말하지 않는 얼굴 (입만 변경)');
        setSpeaking(false);
        // 눈 상태는 변경하지 않음
        setLastPayload({ speaking: false });
        setLastUpdated(Date.now());
      });
    },
    [head]
  );

  const cleanupSocket = useCallback(() => {
    if (socketRef.current) {
      socketRef.current.removeAllListeners();
      socketRef.current.disconnect();
    }
    socketRef.current = null;
    setStatus('closed');
  }, []);

  useEffect(() => {
    if (!enabled) {
      cleanupSocket();
      return undefined;
    }

    setStatus('connecting');
    setError(null);

    const token = isBrowser ? localStorage.getItem('access_token') : null;
    
    // 토큰이 없으면 연결하지 않음
    if (!token) {
      console.error('❌ [로봇 표정 소켓] 토큰이 없습니다.');
      setError('로그인이 필요합니다.');
      setStatus('error');
      return undefined;
    }

    console.log('🔄 [로봇 표정 소켓] 연결 시도 중...');
    
    // 기본 네임스페이스(/)로 연결 (백엔드에서 기본 네임스페이스만 사용)
    const socket = io(DEFAULT_SOCKET_URL, {
      path: DEFAULT_SOCKET_PATH,
      transports: ['websocket'],
      autoConnect: false,
      reconnection: autoReconnect,
      reconnectionDelay: reconnectDelayMs,
      query: {
        head: head ? 'true' : 'false',
      },
      auth: {
        token,
        session_type: 'robot_head',
      },
    });

    registerHandlers(socket);
    socket.connect();
    socketRef.current = socket;

    return () => {
      cleanupSocket();
    };
  }, [autoReconnect, cleanupSocket, enabled, head, reconnectDelayMs, registerHandlers]);

  const connect = useCallback(() => {
    if (!enabled) {
      return;
    }
    if (!socketRef.current) {
      return;
    }
    if (!socketRef.current.connected) {
      setStatus('connecting');
      socketRef.current.connect();
    }
  }, [enabled]);

  const disconnect = useCallback(() => {
    if (socketRef.current?.connected) {
      socketRef.current.disconnect();
      setStatus('closed');
    }
  }, []);

  useEffect(() => {
    if (!enabled) {
      setEmotion('neutral');
      setSpeaking(false);
      setLastPayload(null);
      setLastUpdated(null);
    }
  }, [enabled]);

  return {
    status,
    emotion,
    speaking,
    lastPayload,
    lastUpdated,
    error,
    connect,
    disconnect,
  };
};
