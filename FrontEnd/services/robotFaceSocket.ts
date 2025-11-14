import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { io, Socket } from 'socket.io-client';

const DEFAULT_SOCKET_URL = process.env.NEXT_PUBLIC_ROBOT_FACE_SOCKET_URL || 'https://k13a408.p.ssafy.io';
const DEFAULT_SOCKET_NAMESPACE = process.env.NEXT_PUBLIC_ROBOT_FACE_SOCKET_NAMESPACE || '/robot-face';
const DEFAULT_SOCKET_PATH = process.env.NEXT_PUBLIC_ROBOT_FACE_SOCKET_PATH || '/socket.io';
const DEFAULT_EMOTION_EVENT = process.env.NEXT_PUBLIC_ROBOT_FACE_EVENT || 'robot-face:emotion';
const DEFAULT_REGISTER_EVENT = process.env.NEXT_PUBLIC_ROBOT_FACE_REGISTER_EVENT || 'robot-face:register';

export type RobotEmotion = 'neutral' | 'happy' | 'sad';

export interface RobotFacePayload {
  type?: string;
  emotion?: RobotEmotion;
  message?: string;
  confidence?: number;
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
  emotion: RobotEmotion;
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
  const [lastPayload, setLastPayload] = useState<RobotFacePayload | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<number | null>(null);
  const socketRef = useRef<Socket | null>(null);

  const registerHandlers = useCallback(
    (socket: Socket) => {
      socket.on('connect', () => {
        setStatus('open');
        setError(null);
        socket.emit(DEFAULT_REGISTER_EVENT, { head });
      });

      socket.on('disconnect', () => {
        setStatus('closed');
      });

      socket.on('connect_error', err => {
        console.error('로봇 표정 소켓 연결 오류:', err);
        setError(err?.message ?? '웹소켓 연결 중 오류가 발생했습니다.');
        setStatus('error');
      });

      socket.on(DEFAULT_EMOTION_EVENT, (payload: RobotFacePayload) => {
        setLastPayload(payload);
        if (payload?.emotion) {
          setEmotion(payload.emotion);
        }
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
    const url = `${DEFAULT_SOCKET_URL}${DEFAULT_SOCKET_NAMESPACE.startsWith('/') ? '' : '/'}${DEFAULT_SOCKET_NAMESPACE}`;

    const socket = io(url, {
      path: DEFAULT_SOCKET_PATH,
      transports: ['websocket'],
      autoConnect: false,
      reconnection: autoReconnect,
      reconnectionDelay: reconnectDelayMs,
      query: {
        head: head ? 'true' : 'false',
      },
      auth: token ? { token } : undefined,
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
      setLastPayload(null);
      setLastUpdated(null);
    }
  }, [enabled]);

  return {
    status,
    emotion,
    lastPayload,
    lastUpdated,
    error,
    connect,
    disconnect,
  };
};
