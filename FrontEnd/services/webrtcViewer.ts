import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { io, Socket } from 'socket.io-client';
import { childApi, robotApi, ChildInfo } from '@/services/api';

const SIGNALING_BASE_URL =
  'https://k13a408.p.ssafy.io';

const TEST_ACCESS_TOKEN = process.env.NEXT_PUBLIC_WEBRTC_TEST_TOKEN || null;
const TEST_ROBOT_ID_ENV = process.env.NEXT_PUBLIC_WEBRTC_TEST_ROBOT_ID;

const ConnectEvents = {
  AUTH_SUCCESS: 'auth_success',
  AUTH_FAILURE: 'auth_failure',
} as const;

const WebRTCEvents = {
  REQUEST_CAST: 'client:request_cast',
  ACCEPT_REQUEST: 'client:accept_request',
  REJECT_REQUEST: 'client:reject_request',
  CAST_REQUESTED: 'server:cast_requested',
  CAST_ACCEPTED: 'server:cast_accepted',
  CAST_REJECTED: 'server:cast_rejected',
  READY_FOR_OFFER: 'client:ready_for_offer',
  PEER_IS_READY: 'server:peer_is_ready',
  SEND_OFFER: 'client:send_offer',
  SEND_ANSWER: 'client:send_answer',
  NEW_OFFER: 'server:new_offer',
  NEW_ANSWER: 'server:new_answer',
  SEND_ICE_CANDIDATE: 'client:send_ice_candidate',
  NEW_ICE_CANDIDATE: 'server:new_ice_candidate',
  CAST_ENDED: 'server:cast_ended',
} as const;

const SessionType = {
  ROBOT: 'robot',
  PARENT: 'parent',
} as const;

type WebRTCStatus =
  | 'idle'
  | 'initializing'
  | 'requesting'
  | 'streaming'
  | 'ended';

interface UseWebRTCViewerOptions {
  remoteVideoRef: React.RefObject<HTMLVideoElement | null>;
  childInfo?: ChildInfo | null;
  fallbackRobotId?: number;
}

interface UseWebRTCViewerResult {
  start: () => Promise<void>;
  stop: () => void;
  status: WebRTCStatus;
  error: string | null;
  isStreaming: boolean;
  isConnecting: boolean;
  robotSource: 'child' | 'fallback' | null;
  hasRemoteStream: boolean;
}

const ICE_SERVERS: RTCIceServer[] = [
  { urls: ['stun:stun.l.google.com:19302'] },
  {
    urls: ['turn:3.38.103.192'],
    username: 'okeyducky',
    credential: 'a4081234',
  },
];

const isBrowser = typeof window !== 'undefined';

const ensureMediaStream = () => new MediaStream();

const resolveRobotIdFromChild = (child?: ChildInfo | null): number | null => {
  const id = child?.robot?.robot_id;
  return typeof id === 'number' && !Number.isNaN(id) ? id : null;
};

export const useWebRTCViewer = ({
  remoteVideoRef,
  childInfo,
  fallbackRobotId,
}: UseWebRTCViewerOptions): UseWebRTCViewerResult => {
  const socketRef = useRef<Socket | null>(null);
  const peerConnectionRef = useRef<RTCPeerConnection | null>(null);
  const robotIdRef = useRef<number | null>(null);
  const [status, setStatus] = useState<WebRTCStatus>('idle');
  const [error, setError] = useState<string | null>(null);
  const [robotSource, setRobotSource] = useState<'child' | 'fallback' | null>(null);
  const [remoteStream, setRemoteStream] = useState<MediaStream | null>(null);
  const memoizedChildRobotId = useMemo(() => resolveRobotIdFromChild(childInfo), [childInfo]);

  const resetVideo = useCallback(() => {
    if (remoteVideoRef.current) {
      remoteVideoRef.current.srcObject = null;
    }
    setRemoteStream(prev => {
      if (prev) {
        prev.getTracks().forEach(track => track.stop());
      }
      return null;
    });
  }, [remoteVideoRef]);

  const cleanupPeerConnection = useCallback(() => {
    if (peerConnectionRef.current) {
      try {
        peerConnectionRef.current.ontrack = null;
        peerConnectionRef.current.onicecandidate = null;
        peerConnectionRef.current.onconnectionstatechange = null;
        peerConnectionRef.current.oniceconnectionstatechange = null;
        peerConnectionRef.current.close();
      } catch {
        // ignore close errors
      }
    }
    peerConnectionRef.current = null;
    resetVideo();
  }, [resetVideo]);

  const cleanupSocket = useCallback(() => {
    if (socketRef.current) {
      try {
        socketRef.current.removeAllListeners();
        socketRef.current.disconnect();
      } catch {
        // ignore disconnect errors
      }
    }
    socketRef.current = null;
  }, []);

  const stop = useCallback(() => {
    cleanupPeerConnection();
    cleanupSocket();
    setRobotSource(null);
    setStatus('ended');
  }, [cleanupPeerConnection, cleanupSocket]);

  const ensureRobotId = useCallback(async () => {
    if (robotIdRef.current) {
      return robotIdRef.current;
    }

    // 1. fallbackRobotId가 명시적으로 전달된 경우 우선 사용
    if (typeof fallbackRobotId === 'number' && !Number.isNaN(fallbackRobotId)) {
      robotIdRef.current = fallbackRobotId;
      setRobotSource('fallback');
      return robotIdRef.current;
    }

    // 2. 환경 변수로 지정된 경우 사용
    if (typeof TEST_ROBOT_ID_ENV === 'string' && TEST_ROBOT_ID_ENV.length > 0) {
      const testRobotId = Number(TEST_ROBOT_ID_ENV);
      if (!Number.isNaN(testRobotId)) {
        robotIdRef.current = testRobotId;
        setRobotSource('fallback');
        return robotIdRef.current;
      }
    }

    // 3. childInfo에서 로봇 ID 가져오기
    if (typeof memoizedChildRobotId === 'number') {
      robotIdRef.current = memoizedChildRobotId;
      setRobotSource('child');
      return robotIdRef.current;
    }

    // 4. /robot/me API로 로봇 정보 가져오기
    const robotResponse = await robotApi.getMe();
    if (robotResponse.success && robotResponse.data?.robot_id) {
      robotIdRef.current = robotResponse.data.robot_id;
      setRobotSource('child');
      return robotIdRef.current;
    }

    // 5. /users/child API로 아이 정보 가져오기 (하위 호환성)
    const childResponse = await childApi.getChild();
    if (childResponse.success && childResponse.data?.robot?.robot_id) {
      robotIdRef.current = childResponse.data.robot.robot_id;
      setRobotSource('child');
      return robotIdRef.current;
    }

    throw new Error(robotResponse.message || childResponse.message || '연결할 로봇을 찾을 수 없습니다.');
  }, [fallbackRobotId, memoizedChildRobotId]);

  const createPeerConnection = useCallback(() => {
    const peerConnection = new RTCPeerConnection({
      iceServers: ICE_SERVERS,
    });

    peerConnection.addEventListener('track', event => {
      const [stream] = event.streams;
      if (!stream) {
        const fallbackStream = new MediaStream([event.track]);
        setRemoteStream(fallbackStream);
        return;
      }

      setRemoteStream(prev => {
        const nextStream = prev ? new MediaStream(prev.getTracks()) : ensureMediaStream();
        stream.getTracks().forEach(track => {
          const exists = nextStream.getTracks().some(existing => existing.id === track.id);
          if (!exists) {
            nextStream.addTrack(track);
          }
        });
        return nextStream;
      });
    });

    peerConnection.addEventListener('connectionstatechange', () => {
      if (!peerConnectionRef.current) {
        return;
      }

      const { connectionState } = peerConnectionRef.current;

      if (connectionState === 'connected') {
        setStatus('streaming');
      } else if (connectionState === 'failed' || connectionState === 'disconnected') {
        setError('영상 연결이 종료되었습니다.');
        stop();
      }
    });

    peerConnection.addEventListener('iceconnectionstatechange', () => {
      // For debugging/logging purposes if needed
    });

    peerConnectionRef.current = peerConnection;
    return peerConnection;
  }, [remoteVideoRef, stop]);

  const registerSocketHandlers = useCallback(
    (socket: Socket) => {
      socket.on('connect', () => {
        setStatus('requesting');
      });

      socket.on('connect_error', err => {
        const errorInfo = err as { message?: string; description?: unknown; data?: unknown };
        console.error(
          'Socket.IO connect error:',
          errorInfo.message ?? err,
          errorInfo.description ?? errorInfo.data ?? null,
        );
        setError('시그널링 서버에 연결할 수 없습니다.');
        stop();
      });

      socket.on('disconnect', () => {
        stop();
      });

      socket.on(ConnectEvents.AUTH_SUCCESS, async () => {
        try {
          const robotId = await ensureRobotId();
          console.log('REQUEST_CAST');
          socket.emit(WebRTCEvents.REQUEST_CAST, SessionType.ROBOT, robotId);
        } catch (authError) {
          setError(
            authError instanceof Error ? authError.message : '로봇 정보를 확인할 수 없습니다.',
          );
          stop();
        }
      });

      socket.on(ConnectEvents.AUTH_FAILURE, message => {
        setError(
          typeof message === 'string' ? message : '인증에 실패했습니다. 다시 로그인해주세요.',
        );
        stop();
      });

      socket.on(WebRTCEvents.CAST_ACCEPTED, async () => {
        try {
          const peerConnection = createPeerConnection();
          const robotId = await ensureRobotId();

          peerConnection.addEventListener('icecandidate', event => {
            if (event.candidate) {
              socket.emit(
                WebRTCEvents.SEND_ICE_CANDIDATE,
                SessionType.ROBOT,
                robotId,
                event.candidate.toJSON(),
              );
            }
          });

          socket.emit(WebRTCEvents.READY_FOR_OFFER, SessionType.ROBOT, robotId);
        } catch (pcError) {
          setError(
            pcError instanceof Error ? pcError.message : 'WebRTC 연결을 초기화할 수 없습니다.',
          );
          stop();
        }
      });

      socket.on(WebRTCEvents.NEW_OFFER, async offerData => {
        try {
          if (!peerConnectionRef.current) {
            throw new Error('PeerConnection이 초기화되지 않았습니다.');
          }

          await peerConnectionRef.current.setRemoteDescription(offerData);
          const answer = await peerConnectionRef.current.createAnswer();
          await peerConnectionRef.current.setLocalDescription(answer);

          const robotId = await ensureRobotId();
          socket.emit(WebRTCEvents.SEND_ANSWER, SessionType.ROBOT, robotId, answer);
        } catch (offerError) {
          console.error('NEW_OFFER 처리 중 오류:', offerError);
          setError('상대방의 연결 요청을 처리할 수 없습니다.');
          stop();
        }
      });

      socket.on(WebRTCEvents.NEW_ICE_CANDIDATE, async (oppType, oppId, data) => {
        if (!peerConnectionRef.current) {
          return;
        }

        const candidateData = data?.candidate || data;
        if (!candidateData) {
          return;
        }

        try {
          await peerConnectionRef.current.addIceCandidate(candidateData);
        } catch (candidateError) {
          console.error('ICE 후보 추가 실패:', candidateError);
        }
      });

      socket.on(WebRTCEvents.CAST_ENDED, () => {
        setError('상대방이 영상 통화를 종료했습니다.');
        stop();
      });
    },
    [createPeerConnection, ensureRobotId, stop],
  );

  const start = useCallback(async () => {
    if (!isBrowser) {
      return;
    }

    if (socketRef.current || peerConnectionRef.current) {
      return;
    }

    setError(null);
    setStatus('initializing');

    const token = localStorage.getItem('access_token');
    if (!token) {
      setError('로그인이 필요합니다. (로그인하거나 NEXT_PUBLIC_WEBRTC_TEST_TOKEN을 설정해주세요.)');
      setStatus('idle');
      return;
    }

    try {
      await ensureRobotId();
    } catch (robotError) {
      setError(robotError instanceof Error ? robotError.message : '로봇 정보를 불러올 수 없습니다.');
      setStatus('idle');
      return;
    }

    try {
      const socket = io(SIGNALING_BASE_URL, {
        path: '/socket.io',
        transports: ['websocket'],
        auth: {
          token,
          session_type: SessionType.PARENT,
        },
      });

      socketRef.current = socket;
      registerSocketHandlers(socket);
    } catch (socketError) {
      console.error('Socket.IO 연결 실패:', socketError);
      setError('시그널링 서버에 연결할 수 없습니다.');
      setStatus('idle');
    }
  }, [ensureRobotId, registerSocketHandlers]);

  useEffect(() => {
    if (!remoteStream || !remoteVideoRef.current) {
      return;
    }

    const videoEl = remoteVideoRef.current;
    videoEl.srcObject = remoteStream;

    const playPromise = videoEl.play();
    if (playPromise && typeof playPromise.then === 'function') {
      playPromise.catch(err => {
        console.warn('비디오 자동 재생이 차단되었습니다. 사용자 인터랙션이 필요할 수 있습니다.', err);
      });
    }

    return () => {
      if (videoEl.srcObject === remoteStream) {
        videoEl.srcObject = null;
      }
    };
  }, [remoteStream, remoteVideoRef]);

  useEffect(() => {
    return () => {
      stop();
    };
  }, [stop]);

  return {
    start,
    stop,
    status,
    error,
    isStreaming: status === 'streaming',
    isConnecting: status === 'initializing' || status === 'requesting',
    robotSource,
    hasRemoteStream: Boolean(remoteStream),
  };
};


