import { useCallback, useEffect, useRef, useState } from 'react';
import { io, Socket } from 'socket.io-client';
import { childApi, ChildInfo } from '@/services/api';

const SIGNALING_BASE_URL =
  process.env.NEXT_PUBLIC_SIGNALING_BASE_URL ||
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  'http://k13a408.p.ssafy.io:8000';

const TEST_ACCESS_TOKEN = process.env.NEXT_PUBLIC_WEBRTC_TEST_TOKEN || null;
const TEST_ROBOT_ID_ENV = process.env.NEXT_PUBLIC_WEBRTC_TEST_ROBOT_ID;
const DEFAULT_FALLBACK_ROBOT_ID =
  typeof TEST_ROBOT_ID_ENV === 'string' && TEST_ROBOT_ID_ENV.length > 0
    ? Number(TEST_ROBOT_ID_ENV)
    : 1;

const ConnectEvents = {
  AUTH_SUCCESS: 'auth_success',
  AUTH_FAILURE: 'auth_failure',
} as const;

const WebRTCEvents = {
  REQUEST_CAST: 'request_cast',
  CAST_ACCEPTED: 'cast_accepted',
  READY_FOR_OFFER: 'ready_for_offer',
  NEW_OFFER: 'new_offer',
  SEND_ANSWER: 'send_answer',
  SEND_ICE_CANDIDATE: 'send_ice_candidate',
  NEW_ICE_CANDIDATE: 'new_ice_candidate',
  CAST_ENDED: 'cast_ended',
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
  remoteVideoRef: React.RefObject<HTMLVideoElement>;
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

export const useWebRTCViewer = ({
  remoteVideoRef,
  childInfo,
  fallbackRobotId,
}: UseWebRTCViewerOptions): UseWebRTCViewerResult => {
  const socketRef = useRef<Socket | null>(null);
  const peerConnectionRef = useRef<RTCPeerConnection | null>(null);
  const remoteStreamRef = useRef<MediaStream | null>(null);
  const robotIdRef = useRef<number | null>(null);
  const [status, setStatus] = useState<WebRTCStatus>('idle');
  const [error, setError] = useState<string | null>(null);
  const [robotSource, setRobotSource] = useState<'child' | 'fallback' | null>(null);

  const resetVideo = useCallback(() => {
    if (remoteVideoRef.current) {
      remoteVideoRef.current.srcObject = null;
    }
    if (remoteStreamRef.current) {
      remoteStreamRef.current.getTracks().forEach(track => track.stop());
      remoteStreamRef.current = null;
    }
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

    if (typeof fallbackRobotId === 'number' && !Number.isNaN(fallbackRobotId)) {
      robotIdRef.current = fallbackRobotId;
      setRobotSource('fallback');
      return robotIdRef.current;
    }

    if (!Number.isNaN(DEFAULT_FALLBACK_ROBOT_ID) && DEFAULT_FALLBACK_ROBOT_ID !== null) {
      robotIdRef.current = DEFAULT_FALLBACK_ROBOT_ID;
      setRobotSource('fallback');
      return robotIdRef.current;
    }

    if (childInfo?.robot?.robot_id) {
      robotIdRef.current = childInfo.robot.robot_id;
      setRobotSource('child');
      return robotIdRef.current;
    }

    const childResponse = await childApi.getChild();
    if (!childResponse.success || !childResponse.data?.robot?.robot_id) {
      throw new Error(childResponse.message || '연결할 로봇을 찾을 수 없습니다.');
    }

    robotIdRef.current = childResponse.data.robot.robot_id;
    setRobotSource('child');
    return robotIdRef.current;
  }, [childInfo, fallbackRobotId]);

  const createPeerConnection = useCallback(() => {
    const peerConnection = new RTCPeerConnection({
      iceServers: ICE_SERVERS,
    });

    remoteStreamRef.current = new MediaStream();
    if (remoteVideoRef.current) {
      remoteVideoRef.current.srcObject = remoteStreamRef.current;
    }

    peerConnection.addEventListener('track', event => {
      const [stream] = event.streams;
      if (!stream) {
        return;
      }

      if (!remoteStreamRef.current) {
        remoteStreamRef.current = new MediaStream();
        if (remoteVideoRef.current) {
          remoteVideoRef.current.srcObject = remoteStreamRef.current;
        }
      }

      const remoteStream = remoteStreamRef.current;
      event.streams.forEach(mediaStream => {
        mediaStream.getTracks().forEach(track => {
          if (!remoteStream.getTracks().includes(track)) {
            remoteStream.addTrack(track);
          }
        });
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
        console.error('Socket.IO connect error:', err);
        setError('시그널링 서버에 연결할 수 없습니다.');
        stop();
      });

      socket.on('disconnect', () => {
        stop();
      });

      socket.on(ConnectEvents.AUTH_SUCCESS, async () => {
        try {
          const robotId = await ensureRobotId();
          socket.emit(WebRTCEvents.REQUEST_CAST, [SessionType.ROBOT, robotId]);
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
              socket.emit(WebRTCEvents.SEND_ICE_CANDIDATE, [
                SessionType.ROBOT,
                robotId,
                event.candidate.toJSON(),
              ]);
            }
          });

          socket.emit(WebRTCEvents.READY_FOR_OFFER, [SessionType.ROBOT, robotId]);
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
          socket.emit(WebRTCEvents.SEND_ANSWER, [SessionType.ROBOT, robotId, answer]);
        } catch (offerError) {
          console.error('NEW_OFFER 처리 중 오류:', offerError);
          setError('상대방의 연결 요청을 처리할 수 없습니다.');
          stop();
        }
      });

      socket.on(WebRTCEvents.NEW_ICE_CANDIDATE, async data => {
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

    const token = localStorage.getItem('access_token') || TEST_ACCESS_TOKEN;
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
  };
};


