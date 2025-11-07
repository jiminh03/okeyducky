import os
from dotenv import load_dotenv
# .env 파일 로드
load_dotenv()

import requests
import sys
import socketio
import time
import threading
from datetime import datetime, date

# [수정] socket_event_schema.py 파일에서 WebRTCEvents를 임포트
from common.schemas.socket_event_schema import WebRTCEvents 

# --- 설정 ---
BASE_URL = os.getenv("TEST_SERV")
DEBUG_PREFIX = "/_manual_test" 

# --- 테스트용 데이터 ---
TS = int(datetime.now().timestamp())
TEST_EMAIL = f"webrtc_test_{TS}@example.com"
TEST_PASSWORD = "pw123"
TEST_ROBOT_SN = f"SN-WEBRTC-{TS}"

# --- Mock SDP/ICE 데이터 ---
mock_offer_data = {"type": "offer", "sdp": f"v=0, o=robot {TS}..."}
mock_answer_data = {"type": "answer", "sdp": f"v=0, o=parent {TS}..."}
mock_ice_robot = {"candidate": f"robot-candidate-{TS}", "sdpMid": "0"}
mock_ice_parent = {"candidate": f"parent-candidate-{TS}", "sdpMid": "0"}

# --- HTTP 클라이언트 (로그인/등록용) ---
http_client = requests.Session()

# --- WebSocket 클라이언트 (시뮬레이션용) ---
sio_robot = socketio.Client(http_session=http_client, reconnection_attempts=3)
sio_parent = socketio.Client(http_session=http_client, reconnection_attempts=3)

# --- 스레드 동기화용 이벤트 ---
robot_auth_done = threading.Event()
parent_auth_done = threading.Event()

# [추가] 새로운 사전 시그널링 단계를 위한 이벤트
cast_requested = threading.Event()  # 부모가 로봇의 요청을 받았는지
cast_accepted = threading.Event()   # 로봇이 부모의 수락을 받았는지

# [기존] SDP/ICE 교환용 이벤트
offer_received_by_parent = threading.Event()
answer_received_by_robot = threading.Event()
ice_received_by_robot = threading.Event()
ice_received_by_parent = threading.Event()

# ===================================================================
# 1. 로봇 (송출) 클라이언트 이벤트 핸들러
# ===================================================================
@sio_robot.event
def connect(): print("🤖 [Robot] WebSocket 연결 성공.")
@sio_robot.event
def disconnect(): print("🔌 [Robot] WebSocket 연결 종료.")

@sio_robot.event
def auth_success():
    print("🔑 [Robot] 'AUTH_SUCCESS' 이벤트 수신!")
    robot_auth_done.set()

# [추가] 부모가 캐스트 요청을 수락했음을 알리는 핸들러
@sio_robot.on(WebRTCEvents.CAST_ACCEPTED)
def on_cast_accepted(data):
    print(f"🤖 [Robot] 'CAST_ACCEPTED' 수신: {data}")
    cast_accepted.set()

@sio_robot.on(WebRTCEvents.NEW_ANSWER)
def on_new_answer(answer):
    print(f"🤖 [Robot] 'NEW_ANSWER' 수신: {answer}")
    assert answer["sdp"] == mock_answer_data["sdp"]
    answer_received_by_robot.set()

@sio_robot.on(WebRTCEvents.NEW_ICE_CANDIDATE)
def on_new_ice_candidate(data):
    print(f"🤖 [Robot] 'NEW_ICE_CANDIDATE' (from Parent) 수신")
    assert data["candidate"] == mock_ice_parent["candidate"]
    ice_received_by_robot.set()

# ===================================================================
# 2. 부모 (수신) 클라이언트 이벤트 핸들러
# ===================================================================
@sio_parent.event
def connect(): print("🧑 [Parent] WebSocket 연결 성공.")
@sio_parent.event
def disconnect(): print("🔌 [Parent] WebSocket 연결 종료.")

@sio_parent.event
def auth_success():
    print("🔑 [Parent] 'AUTH_SUCCESS' 이벤트 수신!")
    parent_auth_done.set()

# [추가] 로봇이 캐스트를 요청했음을 알리는 핸들러
@sio_parent.on(WebRTCEvents.CAST_REQUESTED)
def on_cast_requested(data):
    print(f"🧑 [Parent] 'CAST_REQUESTED' 수신: {data}")
    cast_requested.set()


@sio_parent.on(WebRTCEvents.NEW_OFFER)
def on_new_offer(offer):
    print(f"🧑 [Parent] 'NEW_OFFER' 수신: {offer['type']}")
    assert offer["sdp"] == mock_offer_data["sdp"]
    offer_received_by_parent.set()

@sio_parent.on(WebRTCEvents.NEW_ICE_CANDIDATE)
def on_new_ice_candidate(data):
    print(f"🧑 [Parent] 'NEW_ICE_CANDIDATE' (from Robot) 수신")
    assert data["candidate"] == mock_ice_robot["candidate"]
    ice_received_by_parent.set()

# ===================================================================
# 3. 메인 실행 함수
# ===================================================================
def run_webrtc_test():
    parent_id, child_id, robot_id, access_token = None, None, None, None
    
    try:
        # === 1단계: HTTP로 사전 설정 (회원가입, 로그인, 자녀/로봇 등록) ===
        print("--- [HTTP 1] 회원가입 ---")
        reg_data = {"parent_name": "WebRTC Test", "email": TEST_EMAIL, "password": TEST_PASSWORD}
        resp = http_client.post(f"{BASE_URL}{DEBUG_PREFIX}/auth/register", json=reg_data)
        assert resp.status_code == 200, f"회원가입 실패: {resp.text}"
        parent_id = resp.json()["parent_id"]
        print(f"✅ Parent 생성 (ID: {parent_id})")

        print("--- [HTTP 2] 로그인 (토큰 획득) ---")
        log_data = {"email": TEST_EMAIL, "password": TEST_PASSWORD}
        resp = http_client.post(f"{BASE_URL}{DEBUG_PREFIX}/auth/login", json=log_data)
        assert resp.status_code == 200, f"로그인 실패: {resp.text}"
        access_token = resp.json()["access_token"]
        print(f"✅ 로그인 성공 (Token: {access_token[:10]}...)")
        
        print("--- [HTTP 3] 자녀 등록 ---")
        child_data = {"name": "WebRTC Child", "gender": "male", "birth_date": "2020-01-01", "parent_id": parent_id}
        resp = http_client.post(f"{BASE_URL}{DEBUG_PREFIX}/child", headers={"Authorization": f"Bearer {access_token}"}, json=child_data)
        assert resp.status_code == 200, f"자녀 등록 실패: {resp.text}"
        child_id = resp.json()["child_id"]
        print(f"✅ Child 생성 (ID: {child_id})")

        print("--- [HTTP 4] 로봇 등록 ---")
        robot_data = {"serial_number": TEST_ROBOT_SN, "child_id": child_id}
        resp = http_client.post(f"{BASE_URL}{DEBUG_PREFIX}/robot", headers={"Authorization": f"Bearer {access_token}"}, json=robot_data)
        assert resp.status_code == 200, f"로봇 등록 실패: {resp.text}"
        robot_id = resp.json()["robot_id"]
        print(f"✅ Robot 생성 (ID: {robot_id})")

        print("--- [HTTP 5] 로봇 로그인 (토큰 획득) ---")
        log_data = {"robot_id": robot_id, "serial_number": TEST_ROBOT_SN}
        resp = http_client.post(f"{BASE_URL}{DEBUG_PREFIX}/auth/login/robot", json=log_data)
        assert resp.status_code == 200, f"로그인 실패: {resp.text}"
        robot_access_token = resp.json()["access_token"]
        print(f"✅ 로그인 성공 (Token: {robot_access_token[:10]}...)")
        
        # === 2단계: WebSocket 연결 및 인증 ===
        print("\n--- [WS 1] 로봇/부모 동시 연결 및 인증 ---")
        auth_robot = {"token": robot_access_token, "session_type": "robot"}
        auth_parent = {"token": access_token, "session_type": "parent"}
        
        sio_robot.connect(BASE_URL, auth=auth_robot)
        sio_parent.connect(BASE_URL, auth=auth_parent)
        
        if not robot_auth_done.wait(timeout=5) or not parent_auth_done.wait(timeout=5):
            raise Exception("WebSocket 인증 타임아웃")
        print("✅ 로봇/부모 인증 동시 성공!")

        # === 3단계: [신규] 사전 시그널링 (캐스트 요청/수락) ===
        print("\n--- [WebRTC 1] 캐스트 요청 및 수락 ---")
        print("🤖 [Robot] SENDS: REQUEST_CAST (to Parent)")
        # webrtc_event.py의 on_request_cast 인자 (opp_clnt_type, opp_clnt_id)
        sio_robot.emit(WebRTCEvents.REQUEST_CAST, ("parent", parent_id))
        
        if not cast_requested.wait(timeout=5):
            raise Exception("🧑 [Parent] 'CAST_REQUESTED' 수신 타임아웃")
        print("✅ 부모가 로봇의 요청을 수신했습니다.")

        print("🧑 [Parent] SENDS: ACCPET_REQUEST (to Robot)")
        # webrtc_event.py의 on_accept_request 인자 (opp_clnt_type, opp_clnt_id)
        sio_parent.emit(WebRTCEvents.ACCPET_REQUEST, ("robot", robot_id))
        
        if not cast_accepted.wait(timeout=5):
            raise Exception("🤖 [Robot] 'CAST_ACCEPTED' 수신 타임아웃")
        print("✅ 로봇이 부모의 수락을 수신했습니다. (양측 준비 완료)")

        # === 4단계: [기존] WebRTC 시그널링 (SDP/ICE) ===
        
        # (Offer) 로봇 -> 서버 -> 부모
        print("\n--- [WebRTC 2] Offer 교환 ---")
        print("🤖 [Robot] SENDS: SEND_OFFER")
        sio_robot.emit(WebRTCEvents.SEND_OFFER,("parent", parent_id, mock_offer_data))
        
        # (경고)
        # on_send_offer 핸들러가 NEW_OFFER를 부모에게 emit하지 않으면
        # 이 부분에서 테스트가 타임아웃으로 실패합니다. (하단 경고 참조)
        if not offer_received_by_parent.wait(timeout=5):
            raise Exception("🧑 [Parent] 'NEW_OFFER' 수신 타임아웃 (서버 로직 확인 필요)")
        print("✅ Offer 교환 성공!")

        # (Answer) 부모 -> 서버 -> 로봇
        print("\n--- [WebRTC 3] Answer 교환 ---")
        print("🧑 [Parent] SENDS: SEND_ANSWER")
        sio_parent.emit(WebRTCEvents.SEND_ANSWER, ("robot", robot_id, mock_answer_data))
        
        if not answer_received_by_robot.wait(timeout=5):
            raise Exception("🤖 [Robot] 'NEW_ANSWER' 수신 타임아웃")
        print("✅ Answer 교환 성공!")
        
        # (ICE) 양방향
        print("\n--- [WebRTC 4] ICE 교환 ---")
        print("🤖 [Robot] SENDS: SEND_ICE_CANDIDATE (to Parent)")
        sio_robot.emit(WebRTCEvents.SEND_ICE_CANDIDATE, ("parent", parent_id, mock_ice_robot))
        
        print("🧑 [Parent] SENDS: SEND_ICE_CANDIDATE (to Robot)")
        sio_parent.emit(WebRTCEvents.SEND_ICE_CANDIDATE, ("robot", robot_id, mock_ice_parent))

        if not ice_received_by_parent.wait(timeout=5) or not ice_received_by_robot.wait(timeout=5):
            raise Exception("🧊 [ICE] 교환 타임아웃")
        print("✅ ICE Candidate 교환 성공!")

        print("\n--- ✨ 모든 WebRTC 테스트 시나리오 성공! ✨ ---")

    except Exception as e:
        print(f"\n--- 🚨 테스트 중단: {e} ---")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        # === 5단계: 클린업 ===
        print("--- 🧹 클린업: 모든 연결 종료 ---")
        if sio_robot.connected: sio_robot.disconnect()
        if sio_parent.connected: sio_parent.disconnect()
        
        if parent_id and access_token:
            print(f"--- 🧹 클린업: Parent (ID: {parent_id}) 삭제 (필요시 구현) ---")
            
if __name__ == "__main__":
    run_webrtc_test()