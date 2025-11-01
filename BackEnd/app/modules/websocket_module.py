import socketio

# Socket.IO 서버 인스턴스를 여기서 생성합니다.
sio = socketio.AsyncServer(
    async_mode='asgi',
    # async_mode: 서버가 실행될 비동기 모드를 지정합니다.
    # 'asgi': FastAPI, Starlette, Uvicorn 등과 같은 ASGI 프레임워크와 통합됨을 의미합니다.
    # (다른 옵션: 'wsgi', 'eventlet', 'gevent' 등)

    cors_allowed_origins='*'
    # cors_allowed_origins: CORS(Cross-Origin Resource Sharing) 설정을 지정합니다.
    # '*' : 모든 도메인(origin)에서의 연결을 허용합니다. 
    #       개발 시에는 편리하지만, 프로덕션 환경에서는 보안을 위해
    #       특정 도메인 목록을 지정하는 것이 좋습니다.
)

# (참고) sio 인스턴스를 생성한 후, 이를 ASGI 애플리케이션(예: FastAPI)에 연결(mount)하여 사용합니다.