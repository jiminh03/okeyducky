import asyncio
import os
from datetime import date, datetime
from dotenv import load_dotenv
import sys
import traceback

# --- 1. 환경 설정 및 경로 설정 ---

# .env 파일 로드 (db_instance.py가 환경 변수를 사용하므로 필수)
print(f"현재 작업 폴더: {os.getcwd()}")
if not os.path.exists('.env'):
    print("경고: .env 파일을 찾을 수 없습니다. 스크립트가 .env 파일과 같은 위치에 있는지 확인하세요.")
load_dotenv()

# 스크립트가 'common'과 'app' 폴더를 찾을 수 있도록 
# 프로젝트 루트를 Python 경로에 추가합니다.
# (이미 설정되어 있다면 이 부분은 불필요할 수 있습니다.)
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# --- 2. 필요한 모듈 임포트 ---
try:
    # DB 인스턴스 (가장 먼저 임포트)
    from common.modules.db_instance import db
    
    # 리포지토리
    from common.repo.user_repo import ParentRepo, ChildRepo
    from common.repo.robot_repo import RobotRepo
    from common.repo.dialogue_repo import DialogueRepo
    
    # 스키마
    from common.schemas.user_schema import *
    from common.schemas.robot_schema import *
    from common.schemas.dialogue_schema import *
    
except ImportError as e:
    print(f"\n--- 🚨 임포트 오류 ---")
    print(f"오류: {e}")
    print("스크립트가 프로젝트 루트에 있는지,")
    print("또는 'common', 'user_repo.py' 등의 파일/폴더 구조가 올바른지 확인하세요.")
    print("가정된 구조: ./common, ./user_repo.py, ./robot_repo.py 등")
    sys.exit(1)


# --- 3. 테스트용 목(Mock) 데이터 ---

# 테스트 실행 시마다 고유한 값을 생성하기 위한 타임스탬프
TS = int(datetime.now().timestamp())

mock_parent_data = ParentRegisterRequest(
    parent_name="Test Parent", 
    email=f"test_parent_{TS}@test.com", 
    password="pw123"
)
mock_child_data = ChildRegisterRequest(
    name="Test Child", 
    gender="M",  # user_schema.py의 ChildRegisterRequest 사용 (enum 대신 str 가정)
    birth_date=date(2020, 1, 1), 
    school="Test School", 
    parent_id=0 # 나중에 채워짐
)
mock_robot_data = RobotRegisterRequest(
    serial_number=f"TEST_SN_{TS}", 
    child_id=0 # 나중에 채워짐
)
mock_dialogue_log_data = DialogueLogBase(speaker="user", message="Hello test message")
mock_report_data = DailyReportCreate(
    date=date.today(), 
    child_id=0, # 나중에 채워짐
    dialogue_logs=[mock_dialogue_log_data]
)


async def main():
    """리포지토리 검증 메인 함수"""
    
    print("--- 🚀 리포지토리 검증 스크립트 시작 ---")
    
    # 1. 데이터베이스 테이블 생성 (main.py의 lifespan과 동일)
    print("Initializing database tables...")
    await db.create_db_and_tables()
    print("✅ Tables initialized.")

    # 2. DB 세션 가져오기
    session = None
    async for s in db.get_session():
        session = s
        break
    
    if not session:
        print("--- 🚨 FATAL: 데이터베이스 세션을 가져올 수 없습니다. ---")
        return

    print(f"✅ DB Session acquired: {session}")

    # 3. 리포지토리 인스턴스 생성
    # (테스트 스크립트에서는 Depends 대신 세션을 직접 주입합니다)
    parent_repo = ParentRepo(session)
    child_repo = ChildRepo(session)
    robot_repo = RobotRepo(session)
    dialogue_repo = DialogueRepo(session)

    # 4. 생성된 데이터 ID 추적 (클린업용)
    created_parent_id = None
    created_child_id = None
    created_robot_id = None
    created_report_id = None

    try:
        # === 5. ParentRepo 검증 ===
        print("\n--- 🧪 ParentRepo 검증 시작 ---")
        
        # Create
        print(f"Creating parent: {mock_parent_data.email}...")
        new_parent = await parent_repo.create_parent(mock_parent_data)
        created_parent_id = new_parent.user_id # user_schema.py: ParentInfoResponse.user_id
        assert new_parent.email == mock_parent_data.email
        print(f"✅ [C] Create Parent OK (ID: {created_parent_id})")

        # Get by ID
        parent_by_id = await parent_repo.get_parent_by_id(created_parent_id)
        assert parent_by_id is not None
        assert parent_by_id.user_id == created_parent_id
        print(f"✅ [R] Get Parent by ID OK")

        # Get by Email
        parent_by_email = await parent_repo.get_parent_by_email(mock_parent_data.email)
        assert parent_by_email is not None
        assert parent_by_email.email == mock_parent_data.email
        print(f"✅ [R] Get Parent by Email OK")

        # Update
        update_req = ParentUpdateRequest(parent_name="Updated Test Parent Name")
        updated_parent = await parent_repo.update_parent(created_parent_id, update_req)
        assert updated_parent.parent_name == "Updated Test Parent Name"
        print(f"✅ [U] Update Parent OK")

        # === 6. ChildRepo 검증 ===
        print("\n--- 🧪 ChildRepo 검증 시작 ---")
        mock_child_data.parent_id = created_parent_id # 부모 ID 연결
        
        # Create
        print(f"Creating child for parent {created_parent_id}...")
        new_child = await child_repo.create_child(mock_child_data)
        created_child_id = new_child.child_id # user_schema.py: ChildInfoResponse.child_id
        assert new_child.name == "Test Child"
        print(f"✅ [C] Create Child OK (ID: {created_child_id})")

        # Get by ID
        child_by_id = await child_repo.get_child_by_id(created_child_id)
        assert child_by_id is not None
        assert child_by_id.child_id == created_child_id
        print(f"✅ [R] Get Child by ID OK")

        # Get by Parent ID
        children = await child_repo.get_children_by_parent_id(created_parent_id)
        assert len(children) > 0
        assert children[0].child_id == created_child_id
        print(f"✅ [R] Get Children by Parent ID OK")

        # === 7. RobotRepo 검증 ===
        print("\n--- 🧪 RobotRepo 검증 시작 ---")
        mock_robot_data.child_id = created_child_id # 자식 ID 연결
        
        # Create
        print(f"Creating robot ({mock_robot_data.serial_number}) for child {created_child_id}...")
        new_robot = await robot_repo.create_robot(mock_robot_data)
        created_robot_id = new_robot.robot_id
        assert new_robot.serial_number == mock_robot_data.serial_number
        print(f"✅ [C] Create Robot OK (ID: {created_robot_id})")
        
        # Get by Serial Number
        robot_by_sn = await robot_repo.get_robot_by_serial_number(mock_robot_data.serial_number)
        assert robot_by_sn is not None
        assert robot_by_sn.robot_id == created_robot_id
        print(f"✅ [R] Get Robot by Serial Number OK")

        # Update Child ID (Test)
        updated_robot = await robot_repo.update_robot_child_id(created_robot_id, created_child_id)
        assert updated_robot.child_id == created_child_id
        print(f"✅ [U] Update Robot Child ID OK")


        # === 8. DialogueRepo 검증 ===
        print("\n--- 🧪 DialogueRepo 검증 시작 ---")
        mock_report_data.child_id = created_child_id # 자식 ID 연결

        # Create Report (with logs)
        print(f"Creating daily report for child {created_child_id}...")
        new_report = await dialogue_repo.create_daily_report(mock_report_data)
        created_report_id = new_report.report_id
        assert new_report is not None
        # (가정: Model의 relationship이 올바르게 설정되어 refresh 시 dialogue_logs가 로드됨)
        assert len(new_report.dialogue_logs) == 1
        assert new_report.dialogue_logs[0].message == "Hello test message"
        print(f"✅ [C] Create Daily Report OK (ID: {created_report_id})")

        # Get Report by ID
        report_by_id = await dialogue_repo.get_daily_report_by_id(created_report_id)
        assert report_by_id is not None
        assert report_by_id.report_id == created_report_id
        print(f"✅ [R] Get Daily Report by ID OK")

        # Get Report by Date Range
        today = date.today()
        reports_by_date = await dialogue_repo.get_daily_reports_by_child_id_and_date_range(
            created_child_id, today, today
        )
        assert len(reports_by_date) > 0
        assert reports_by_date[0].report_id == created_report_id
        print(f"✅ [R] Get Reports by Date Range OK")

        # Update Report
        report_update = DailyReportUpdateRequest(daily_summary="Updated summary.")
        updated_report = await dialogue_repo.update_daily_report(created_report_id, report_update)
        assert updated_report.daily_summary == "Updated summary."
        print(f"✅ [U] Update Daily Report OK")

        print("\n--- ✨ 모든 리포지토리 검증 성공! ✨ ---")

    except Exception as e:
        print(f"\n--- 🚨 VALIDATION FAILED 🚨 ---")
        print(f"Error: {e}")
        traceback.print_exc()

    finally:
        # === 9. 클린업 ===
        print("\n--- 🧹 데이터 클린업 시작 ---")
        if created_parent_id:
            # Parent를 삭제하면 FK 제약조건(CASCADE)에 따라
            # Child, Robot, Report 등이 함께 삭제되어야 합니다.
            # (DB 테이블의 FK에 ON DELETE CASCADE가 설정되었다고 가정)
            print(f"Deleting parent ID: {created_parent_id} (and cascading)...")
            deleted = await parent_repo.delete_parent(created_parent_id)
            print(f"✅ Cleanup OK: {deleted}")
        
        await session.close()
        print("DB Session closed.")
        print("--- 🏁 검증 스크립트 종료 ---")


if __name__ == "__main__":
    # 스크립트 실행 (예: python validate_repos.py)
    asyncio.run(main())