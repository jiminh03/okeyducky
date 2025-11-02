import requests
import sys
from datetime import datetime, date
import socketio  
import time

from common.schemas.socket_event_schema import ConnectEvents     

# --- 설정 ---
BASE_URL = "http://127.0.0.1:8000" 
DEBUG_PREFIX = "/_manual_test" #

# 타임스탬프로 매번 새로운 이메일/시리얼 생성 (409 Conflict 방지)
TS = int(datetime.now().timestamp())
TEST_EMAIL = f"test_{TS}@example.com"
TEST_PASSWORD = "pw123"
TEST_ROBOT_SN = f"SN-TEST-{TS}"

# --- 세션 및 변수 ---
client = requests.Session()

# ⬇️ [수정] 3. Socket.IO 클라이언트를 *미리* 생성합니다.
#           이때, 'http_session=client'로 설정하여
#           HTTP 세션을 공유하도록 만듭니다.
sio_client = socketio.Client(http_session=client)

access_token = None
parent_id = None
child_id = None
robot_id = None
report_id = None

# (시나리오 요약 주석은 원본과 동일)
# ...

def run_test_scenario():
    """
    'manual_debug_router.py'의 모든 엔드포인트를 순차적으로 테스트합니다.
    """
    
    global access_token, parent_id, child_id, robot_id, report_id
    
    print(f"--- 🚀 자동 검증 스크립트 시작 (대상: {BASE_URL}) ---")
    print(f"테스트용 이메일: {TEST_EMAIL}")
    print(f"테스트용 시리얼: {TEST_ROBOT_SN}\n")
    
    try:
        # === 시나리오 1: [1] 회원가입 ===
        print("--- [1] 회원가입 테스트 (POST /auth/register) ---")
        register_data = {
            "parent_name": "AutoTest Parent",
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        }
        response = client.post(
            f"{BASE_URL}{DEBUG_PREFIX}/auth/register", 
            json=register_data
        )
        if response.status_code != 200:
            raise Exception(f"회원가입 실패! {response.status_code} {response.text}")
            
        parent_id = response.json()["parent_id"]
        print(f"✅ 회원가입 성공! (Parent ID: {parent_id})")

        # === 시나리오 2: [2] 로그인 (토큰 획득) ===
        print("\n--- [2] 로그인 테스트 (POST /auth/login) ---")
        login_data = {"email": TEST_EMAIL, "password": TEST_PASSWORD}
        response = client.post(
            f"{BASE_URL}{DEBUG_PREFIX}/auth/login",
            json=login_data 
        )
        if response.status_code != 200:
            raise Exception(f"로그인 실패! {response.status_code} {response.text} (auth_service.py 수정 필요)")
        
        access_token = response.json()["access_token"]
        print(f"✅ 로그인 성공! (Token: {access_token})")
        client.headers.update({"Authorization": f"Bearer {access_token}"})

        # === 시나리오 3: [3] 인증 테스트 ===
        print("\n--- [3] 인증 테스트 (GET /auth/get_current) ---")
        response = client.get(f"{BASE_URL}{DEBUG_PREFIX}/auth/get_current")
        print(f"Response: {response.status_code} {response.text}")
        if response.status_code != 200:
            raise Exception(f"인증 실패! {response.status_code} {response.text}")
        assert response.json()["parent_id"] == parent_id
        print(f"✅ 'get_current_parent' 인증 성공!")

        # ===================================================================
        # === 시나리오 4: [4] WebSocket 연결 및 인증 테스트 ===
        # ===================================================================
        print("\n--- [4] WebSocket 인증 테스트 (connect + auth) ---")
        
        # (A) 이벤트 핸들러 정의
        # 이 플래그는 비동기 이벤트 핸들러가 성공적으로 호출되었는지 확인하기 위함입니다.
        auth_success_flag = False

        @sio_client.event
        def connect():
            print(f"✅ WebSocket 연결 성공. (SID: {sio_client.sid})")

        @sio_client.on(ConnectEvents.AUTH_SUCCESS)
        def auth_success():
            # ⬅️ (connection_event.py의 'ConnectEvents.AUTH_SUCCESS'에 해당)
            nonlocal auth_success_flag
            print("✅ WebSocket 'AUTH_SUCCESS' 이벤트 수신!")
            auth_success_flag = True
            sio_client.disconnect() # 테스트 성공, 연결 종료

        @sio_client.event
        def connect_error(data):
            print(f"🚨 WebSocket 연결 실패: {data}")
            # 'sio_client.wait()'를 중단시키기 위해 수동으로 연결 종료
            if sio_client.connected:
                sio_client.disconnect()

        @sio_client.event
        def disconnect():
            print("🔌 WebSocket 연결 종료.")

        try:
            # (B) connection_event.py의 'auth' 매개변수와 동일한 auth 페이로드 구성
            auth_payload = {
                "token": access_token, 
                "session_type": "parent" #
            }
            
            # (C) 서버에 연결 시도
            sio_client.connect(
                BASE_URL, 
                auth=auth_payload, 
                transports=['websocket']
            )
            
            # (D) 'sio_client.wait()'는 백그라운드 스레드에서 실행되는 클라이언트가
            # 'sio_client.disconnect()'를 호출할 때까지 이 스크립트를 차단(block)합니다.
            print("WebSocket 연결 및 AUTH_SUCCESS 이벤트 대기 중...")
            sio_client.wait()

            if not auth_success_flag:
                raise Exception("WebSocket 인증 실패 ('AUTH_SUCCESS' 이벤트를 받지 못했습니다)")
            
            print("✅ 'connect' + 'auth_success' 테스트 OK")

        except socketio.exceptions.ConnectionError as e:
            # 서버가 켜져 있지 않거나, 토큰이 유효하지 않아 
            # 'connect' 핸들러에서 서버가 'disconnect'를 호출한 경우
            raise Exception(f"WebSocket 연결 실패! 서버가 인증을 거부했을 수 있습니다. (에러: {e})")
        except Exception as e:
            raise Exception(f"WebSocket 테스트 중 오류: {e}")
        # ===================================================================

        # === 시나리오 5: [5] 자녀 등록 (인가 테스트) ===
        print("\n--- [5] 자녀 등록 테스트 (POST /child) ---")
        
        # (A) 실패 테스트 (403 NotOwnerError)
        child_data_fail = {
            "name": "Bad Child", "gender": "male", 
            "birth_date": "2020-01-01", "parent_id": 12345
        }
        response = client.post(f"{BASE_URL}{DEBUG_PREFIX}/child", json=child_data_fail)
        assert response.status_code == 403 # 403 Forbidden (NotOwnerError)
        print("✅ 자녀 등록 (인가 실패, 403) 테스트 OK")

        # (B) 성공 테스트
        child_data_success = {
            "name": "My Auto Child", "gender": "female", 
            "birth_date": "2021-02-02", "parent_id": parent_id
        }
        response = client.post(f"{BASE_URL}{DEBUG_PREFIX}/child", json=child_data_success)
        if response.status_code != 200:
            raise Exception(f"자녀 등록 실패! {response.status_code} {response.text}")
            
        child_id = response.json()["child_id"]
        print(f"✅ 자녀 등록 (성공) OK (Child ID: {child_id})")

        # === 시나리오 6: [6] 자녀 목록 조회 ===
        print("\n--- [6] 자녀 목록 테스트 (GET /child/list) ---")
        response = client.get(f"{BASE_URL}{DEBUG_PREFIX}/child/list")
        if response.status_code != 200:
            raise Exception(f"자녀 목록 조회 실패! {response.status_code} {response.text}")
        
        assert len(response.json()) == 1
        assert response.json()[0]["child_id"] == child_id
        print("✅ 'get_child_list' 테스트 OK")

        # === 시나리오 7: [7] 자녀 정보 조회 ===
        print("\n--- [7] 자녀 정보 조회 테스트 (GET /child/{id}) ---")
        response = client.get(f"{BASE_URL}{DEBUG_PREFIX}/child/{child_id}")
        assert response.status_code == 200
        assert response.json()["name"] == "My Auto Child"
        print("✅ 'get_child_info' (성공) 테스트 OK")

        # (실패 테스트 - 404 Not Found)
        response = client.get(f"{BASE_URL}{DEBUG_PREFIX}/child/999999")
        assert response.status_code == 404 # 404 Not Found (ChildNotFound)
        print("✅ 'get_child_info' (실패 404) 테스트 OK")

        # === 시나리오 8: [8] 로봇 등록 ===
        print("\n--- [8] 로봇 등록 테스트 (POST /robot) ---")
        robot_data = {
            "serial_number": TEST_ROBOT_SN, 
            "child_id": child_id
        }
        response = client.post(f"{BASE_URL}{DEBUG_PREFIX}/robot", json=robot_data)
        if response.status_code != 200:
            raise Exception(f"로봇 등록 실패! {response.status_code} {response.text} (robot_service.py 버그 확인!)")
        
        robot_id = response.json()["robot_id"]
        print(f"✅ 'register_robot' (성공) 테스트 OK (Robot ID: {robot_id})")
        
        # (실패 테스트 - 409 Conflict)
        response = client.post(f"{BASE_URL}{DEBUG_PREFIX}/robot", json=robot_data)
        assert response.status_code == 409 # 409 Conflict (시리얼 중복)
        print("✅ 'register_robot' (실패 409) 테스트 OK")

        # === 시나리오 9: [9] 로봇 정보 조회 ===
        print("\n--- [9] 로봇 정보 조회 테스트 (GET /robot) ---")
        response = client.get(f"{BASE_URL}{DEBUG_PREFIX}/robot?serial_number={TEST_ROBOT_SN}")
        if response.status_code != 200:
            raise Exception(f"로봇 조회 실패! {response.status_code} {response.text} (robot_service.py 버그 확인!)")
        assert response.json()["robot_id"] == robot_id
        print("✅ 'get_robot_info' (성공) 테스트 OK")

        # === 시나리오 10: (Dialogue) 리포트 생성 (인증 불필요) ===
        print("\n--- [10] 리포트 생성 테스트 (POST /dialogue/report) ---")
        today = date.today().isoformat()
        report_data = {
            "date": today,
            "child_id": child_id,
            "dialogue_logs": [
                {"speaker": "user", "message": "Hello"},
                {"speaker": "robot", "message": "Hi!"}
            ]
        }
        response = client.post(f"{BASE_URL}{DEBUG_PREFIX}/dialogue/report", json=report_data)
        if response.status_code != 200:
            raise Exception(f"리포트 생성 실패! {response.status_code} {response.text}")
        
        report_id = response.json()["report_id"]
        assert len(response.json()["dialogue_logs"]) == 2
        print(f"✅ 'register_daily_report' (성공) 테스트 OK (Report ID: {report_id})")

        # === 시나리오 11: [10] 리포트 ID로 조회 (인증 필요) ===
        print("\n--- [10] 리포트 ID 조회 테스트 (GET /dialogue/report/{id}) ---")
        response = client.get(f"{BASE_URL}{DEBUG_PREFIX}/dialogue/report/{report_id}")
        assert response.status_code == 200
        assert response.json()["report_id"] == report_id
        print("✅ 'get_daily_report_by_id' (성공) 테스트 OK")

        # === 시나리오 12: [11] 리포트 Child ID로 조회 (인증 필요) ===
        print("\n--- [11] 리포트 Child ID 조회 테스트 (GET /dialogue/report/by-child/{id}) ---")
        params = {"start_date": today, "end_date": today}
        response = client.get(
            f"{BASE_URL}{DEBUG_PREFIX}/dialogue/report/by-child/{child_id}",
            params=params
        )
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["report_id"] == report_id
        print("✅ 'get_daily_report_by_child_id' (성공) 테스트 OK")

        print("\n--- ✨ 모든 자동 검증 시나리오 성공! ✨ ---")

    except requests.exceptions.ConnectionError:
        print(f"--- 🚨 연결 실패: '{BASE_URL}'에 서버가 실행되고 있는지 확인하세요. ---")
        sys.exit(1)
    except Exception as e:
        print(f"\n--- 🚨 테스트 중단: {e} ---")
        import traceback
        traceback.print_exc() # ⬅️ 디버깅을 위해 전체 트레이스백 출력
        sys.exit(1)

if __name__ == "__main__":
    run_test_scenario()