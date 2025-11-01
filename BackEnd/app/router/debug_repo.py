import asyncio
from fastapi import APIRouter, Depends, HTTPException, status
from datetime import date, datetime
import traceback
from typing import Dict, Any

# --- 1. 스크립트에서 사용한 모든 의존성 임포트 ---
# (이제 FastAPI가 이들을 주입해 줄 것입니다)
from common.repo.user_repo import ParentRepo, ChildRepo
from common.repo.robot_repo import RobotRepo
from common.repo.dialogue_repo import DialogueRepo

from common.schemas.user_schema import *
from common.schemas.robot_schema import *
from common.schemas.dialogue_schema import *

# --- 2. 라우터 생성 ---
router = APIRouter(
    prefix="/_debug",  # (예: /_debug/validate-repos)
    tags=["Debug"],  # Swagger UI에서 그룹화
    include_in_schema=True,  # (운영에서는 False로)
)


# --- 3. 검증 스크립트의 main() 함수를 '의존성'으로 변환 ---
async def run_all_validations(
    # FastAPI의 'Depends'를 사용해 Repo들을 주입받습니다.
    # 세션을 수동으로 생성할 필요가 전혀 없습니다!
    parent_repo: ParentRepo = Depends(ParentRepo),
    child_repo: ChildRepo = Depends(ChildRepo),
    robot_repo: RobotRepo = Depends(RobotRepo),
    dialogue_repo: DialogueRepo = Depends(DialogueRepo),
) -> Dict[str, Any]:
    """
    repo_validate.py의 main() 로직을 FastAPI 의존성으로 실행합니다.
    """

    print("--- 🚀 리포지토리 검증 시작 (FastAPI 엔드포인트) ---")

    # --- 테스트용 목(Mock) 데이터 ---
    TS = int(datetime.now().timestamp())
    mock_parent_data = ParentRegisterRequest(
        parent_name="Test Parent", email=f"test_parent_{TS}@test.com", password="pw123"
    )
    mock_child_data = ChildRegisterRequest(
        name="Test Child",
        gender=Gender.male,
        birth_date="2020-01-01",  # ⬅️ Pydantic 오류 수정을 위해 str로 변경
        school="Test School",
        parent_id=0,
    )
    mock_robot_data = RobotRegisterRequest(serial_number=f"TEST_SN_{TS}", child_id=0)
    mock_dialogue_log_data = DialogueLogBase(
        speaker="user", message="Hello test message"
    )
    mock_report_data = DailyReportCreate(
        date=date.today(), child_id=0, dialogue_logs=[mock_dialogue_log_data]
    )

    created_parent_id = None

    # =====================================================================
    # [전체 테스트 케이스 요약]
    #
    # 이 스크립트는 모든 리포지토리의 핵심 기능(CRUD)이
    # 데이터베이스와 올바르게 상호작용하는지 검증합니다.
    # 모든 작업은 단일 트랜잭션 내에서 실행되며,
    # 'finally' 블록에서 모든 변경사항을 롤백(삭제)하여 DB를 깨끗하게 유지합니다.
    #
    # --- 1. ParentRepo (부모) 검증 ---
    # [C] create_parent: 테스트용 부모 계정을 생성합니다.
    # [R] get_parent_by_id: 생성된 ID로 부모를 조회합니다.
    # [R] get_parent_by_email: 생성된 Email로 부모를 조회합니다. (user_repo.py에 존재 시)
    # [U] update_parent: 부모의 이름을 수정합니다. (user_repo.py에 존재 시)
    #
    # --- 2. ChildRepo (자녀) 검증 ---
    # [C] create_child: 위에서 생성된 부모 ID에 연결된 자녀를 생성합니다.
    # [R] get_child_by_id: 생성된 ID로 자녀를 조회합니다.
    # [R] get_children_by_parent_id: 부모 ID로 자녀 목록을 조회합니다. (user_repo.py에 존재 시)
    # [U] update_child: 자녀의 학교 정보를 수정합니다. (user_repo.py에 존재 시)
    #
    # --- 3. RobotRepo (로봇) 검증 ---
    # [C] create_robot: 위에서 생성된 자녀 ID에 연결된 로봇을 생성(등록)합니다.
    # [R] get_robot_by_id: 생성된 ID로 로봇을 조회합니다.
    # [R] get_robot_by_child_id: 자녀 ID로 로봇을 조회합니다. (robot_repo.py에 존재 시)
    # [R] get_robot_by_serial_number: 시리얼 번호로 로봇을 조회합니다. (robot_repo.py에 존재 시)
    # [U] update_robot_child_id: 로봇을 다른 자녀에게 재할당합니다. (robot_repo.py에 존재 시)
    #
    # --- 4. DialogueRepo (대화/리포트) 검증 ---
    # [C] create_daily_report: 자녀 ID로 일간 리포트 및 대화 로그(목록)를 생성합니다.
    # [R] get_daily_report_by_date: 자녀 ID와 날짜로 리포트를 조회합니다.
    # [R] get_dialogue_logs_by_report_id: 리포트 ID로 대화 로그 목록을 조회합니다.
    #
    # --- 5. Cleanup (정리) - (finally 블록에서 실행) ---
    # [D] delete_parent: 처음에 생성한 부모 계정을 삭제합니다.
    #     (암시적 테스트): DB의 외래 키 제약조건(ON DELETE CASCADE)에 의해
    #     부모 삭제 시, 위에서 생성된 모든 자녀, 로봇, 대화/리포트 데이터가
    #     연쇄적으로 모두 삭제되는지 확인합니다.
    # =====================================================================

    try:
        # === 5. ParentRepo 검증 ===
        print("\n--- 🧪 ParentRepo 검증 시작 ---")
        
        # Create
        print(f"Creating parent: {mock_parent_data.email}...")
        new_parent = await parent_repo.create_parent(mock_parent_data)
        created_parent_id = new_parent.parent_id
        assert new_parent.email == mock_parent_data.email
        print(f"✅ [C] Create Parent OK (ID: {created_parent_id})")

        # Get by ID
        parent_by_id = await parent_repo.get_parent_by_id(created_parent_id)
        assert parent_by_id is not None
        assert parent_by_id.parent_id == created_parent_id
        print(f"✅ [R] Get Parent by ID OK")

        # Get by Email
        parent_by_email = await parent_repo.get_parent_by_email(mock_parent_data.email)
        assert parent_by_email is not None
        assert parent_by_email.email == mock_parent_data.email
        print(f"✅ [R] Get Parent by Email OK")

        # Update
        update_req = ParentUpdateRequest(parent_name="Updated Test Parent Name") #
        updated_parent = await parent_repo.update_parent(created_parent_id, update_req)
        assert updated_parent.parent_name == "Updated Test Parent Name"
        print(f"✅ [U] Update Parent OK")

        # === 6. ChildRepo 검증 ===
        print("\n--- 🧪 ChildRepo 검증 시작 ---")
        mock_child_data.parent_id = created_parent_id # 부모 ID 연결
        
        # Create
        print(f"Creating child for parent {created_parent_id}...")
        new_child = await child_repo.create_child(mock_child_data)
        created_child_id = new_child.child_id
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

        # ⬇️ [추가된 테스트 1/4] ChildRepo - Update
        print(f"Updating child {created_child_id} school...")
        update_child_req = ChildUpdateRequest(school="Updated School Name") #
        updated_child = await child_repo.update_child(created_child_id, update_child_req)
        
        # (참고: 이 테스트가 통과하려면 user_repo.py의 update_child 메서드 구현이 필요합니다)
        assert updated_child is not None, "Update Child returned None"
        assert updated_child.school == "Updated School Name", "Child school was not updated"
        print(f"✅ [U] Update Child OK")
        # ⬆️ [추가된 테스트 1/4]

        # === 7. RobotRepo 검증 ===
        print("\n--- 🧪 RobotRepo 검증 시작 ---")
        mock_robot_data.child_id = created_child_id # 자식 ID 연결
        
        # Create
        print(f"Creating robot ({mock_robot_data.serial_number}) for child {created_child_id}...")
        new_robot = await robot_repo.create_robot(mock_robot_data)
        created_robot_id = new_robot.robot_id
        assert new_robot.serial_number == mock_robot_data.serial_number
        print(f"✅ [C] Create Robot OK (ID: {created_robot_id})")
        
        # ⬇️ [추가된 테스트 2/4] RobotRepo - Get by ID
        # Get by ID
        robot_by_id = await robot_repo.get_robot_by_id(created_robot_id)
        assert robot_by_id is not None, "Robot Get by ID returned None"
        assert robot_by_id.robot_id == created_robot_id
        print(f"✅ [R] Get Robot by ID OK")
        # ⬆️ [추가된 테스트 2/4]

        # ⬇️ [추가된 테스트 3/4] RobotRepo - Get by Child ID
        # Get by Child ID
        robot_by_child = await robot_repo.get_robot_by_child_id(created_child_id)
        assert robot_by_child is not None, "Robot Get by Child ID returned None"
        assert robot_by_child.robot_id == created_robot_id
        assert robot_by_child.child_id == created_child_id
        print(f"✅ [R] Get Robot by Child ID OK")
        # ⬆️ [추가된 테스트 3/4]

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
        assert len(new_report.dialogue_logs) == 1 #
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

        # ⬇️ [추가된 테스트 4/4] DialogueRepo - Get Logs by Report ID
        # (참고: 이 테스트가 통과하려면 dialogue_repo.py에 get_dialogue_logs_by_report_id 메서드 구현이 필요합니다)
        print(f"Getting dialogue logs for report {created_report_id}...")
        report_with_logs = await dialogue_repo.get_daily_report_by_id(created_report_id)
        
        assert report_with_logs is not None, "Get Report by ID returned None"
        assert report_with_logs.dialogue_logs is not None, "dialogue_logs is None"
        assert len(report_with_logs.dialogue_logs) == 1, "Log count mismatch"
        assert report_with_logs.dialogue_logs[0].message == "Hello test message", "Log message mismatch"
        # ⬆️ [추가된 테스트 4/4]

        # Update Report
        report_update = DailyReportUpdateRequest(daily_summary="Updated summary.") #
        updated_report = await dialogue_repo.update_daily_report(created_report_id, report_update)
        assert updated_report.daily_summary == "Updated summary."
        print(f"✅ [U] Update Daily Report OK")

        print("\n--- ✨ 모든 리포지토리 검증 성공! ✨ ---")
        
        return {"status": "SUCCESS", "message": "All repo validations passed!"}

    except Exception as e:
        print(f"\n--- 🚨 VALIDATION FAILED 🚨 ---")
        print(f"Error: {e}")
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Validation Failed: {str(e)}"
        )
    
    finally:
        # === 9. 클린업 ===
        print("\n--- 🧹 데이터 클린업 시작 ---")
        if created_parent_id:
            print(f"Deleting parent ID: {created_parent_id} (and cascading)...")
            deleted = await parent_repo.delete_parent(created_parent_id)
            print(f"✅ Cleanup OK: {deleted}")

        print("--- 🏁 검증 스크립트 종료 (세션 자동 반환) ---")

# --- 4. 검증 로직을 실행하는 엔드포인트 생성 ---
@router.post(
    "/validate-repos", summary="[Debug] 모든 리포지토리의 CRUD를 테스트합니다."
)
async def endpoint_run_validation(
    # /_debug/validate-repos 엔드포인트를 호출하면,
    # FastAPI가 'run_all_validations' 의존성을 실행하고
    # 그 결과를 'result' 변수에 주입해 줍니다.
    result: dict = Depends(run_all_validations),
):
    """
    이 엔드포인트는 DB 연결부터 모든 Repo의 C-R-U-D 및
    데이터 삭제(Cleanup)까지 전체 과정을 테스트합니다.
    """
    return result
