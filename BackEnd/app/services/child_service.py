from fastapi import File, Form, UploadFile
from app.providers.parent_providers import *
from app.providers.child_providers import *
from app.providers.robot_providers import *

from app.services.auth_service import get_current_parent

from app.exceptions import *
from common.schemas.robot_schema import RobotRegisterRequest


async def register_child(
    name: str = Form(...),
    gender: Gender = Form(...),  # 문자열로 오지만 Pydantic이 Enum으로 변환 시도
    birth_date: date = Form(...),
    serial_number: str = Form(...),
    school: Optional[str] = Form(None),
    profile_img: Optional[UploadFile] = File(None),
    parent: Parent = Depends(get_current_parent),
    create_child_service=Depends(get_create_child_service),
    create_robot_service=Depends(get_create_robot_service),
) -> ChildInfoResponse:
    """
    자녀를 등록합니다.

    Args:
        child (ChildRegisterRequest): 자녀 등록 요청 데이터
        parent (Parent, optional): 현재 로그인한 부모님 정보. Defaults to Depends(get_current_parent).
        create_child_service (Depends, optional): 자녀 생성 서비스. Defaults to Depends(get_create_child_service).

    Raises:
        NotOwnerError: 자녀를 등록할 권한이 없을 경우 발생

    Returns:
        ChildInfoResponse: 등록된 자녀 정보
    """

    img_bytes = None
    if profile_img:
        img_bytes = await profile_img.read()
        # (선택 사항) 여기서 파일 크기나 타입 검증 로직을 추가할 수 있습니다.
        # if len(img_bytes) > 5 * 1024 * 1024: ...

    # 5. [조립] 서비스 계층용 순수 DTO 생성
    child_create_info = ChildRegisterRequest(
        name=name,
        gender=gender,
        birth_date=birth_date,
        school=school,
        profile_img=img_bytes,  # 변환된 bytes 주입
        parent_id=parent.parent_id,
    )

    if child_create_info.parent_id != parent.parent_id:
        raise NotOwnerError(detail="자녀를 등록할 권한이 없습니다.")

    child = await create_child_service(child_create_info)

    robot_info = RobotRegisterRequest(
        serial_number=serial_number, child_id=child.child_id
    )

    await create_robot_service(robot_info)

    return child


async def get_child_list(
    parent: Parent = Depends(get_current_parent),
    get_child_list_service=Depends(get_children_by_parent_id_service),
) -> List[ChildInfoResponse]:
    """
    현재 로그인한 부모님의 자녀 목록을 가져옵니다.

    Args:
        parent (Parent, optional): 현재 로그인한 부모님 정보. Defaults to Depends(get_current_parent).
        get_child_list_service (Depends, optional): 부모 ID로 자녀 목록을 가져오는 서비스. Defaults to Depends(get_children_by_parent_id_service).

    Returns:
        List[ChildInfoResponse]: 자녀 정보 목록
    """
    return await get_child_list_service(parent.parent_id)


async def get_child_info(
    child_id: int,
    child_list: List[ChildInfoResponse] = Depends(get_child_list),
    get_child_info_service=Depends(get_child_by_id_service),
) -> ChildInfoResponse:
    """
    특정 자녀의 정보를 가져옵니다.

    Args:
        child_id (int): 자녀 ID
        child_list (List[ChildInfoResponse], optional): 현재 로그인한 부모님의 자녀 목록. Defaults to Depends(get_child_list).
        get_child_info_service (Depends, optional): ID로 자녀 정보를 가져오는 서비스. Defaults to Depends(get_child_by_id_service).

    Raises:
        ChildNotFound: 해당 ID의 자녀를 찾을 수 없을 경우 발생
        NotOwnerError: 해당 자녀 정보에 접근할 권한이 없을 경우 발생

    Returns:
        ChildInfoResponse: 자녀 정보
    """
    child = await get_child_info_service(child_id)
    if child is None:
        raise ChildNotFound

    child_ids = [child.child_id for child in child_list]
    if child_id not in child_ids:
        raise NotOwnerError(detail="해당 자녀 정보에 접근할 권한이 없습니다.")

    return child


async def update_child_info(
    # 1. [입력] 수정할 데이터 (모두 Optional + Form)
    name: Optional[str] = Form(None),
    gender: Optional[Gender] = Form(None),
    birth_date: Optional[date] = Form(None),
    school: Optional[str] = Form(None),
    # 2. [입력] 수정할 프로필 이미지 파일
    profile_img: Optional[UploadFile] = File(None),
    child_list: List[ChildInfoResponse] = Depends(get_child_list),
    update_child_service=Depends(get_update_child_service),
    get_child_info_service=Depends(get_child_by_id_service),
) -> ChildInfoResponse:
    """
    자녀 정보를 수정합니다.

    Args:
        child_id (int): 수정할 자녀 ID
        child (ChildUpdateRequest): 자녀 수정 요청 데이터
        child_list (List[ChildInfoResponse], optional): 현재 로그인한 부모님의 자녀 목록. Defaults to Depends(get_child_list).
        update_child_service (Depends, optional): 자녀 정보 수정 서비스. Defaults to Depends(get_update_child_service).
        get_child_info_service (Depends, optional): ID로 자녀 정보를 가져오는 서비스. Defaults to Depends(get_child_by_id_service).

    Raises:
        ChildNotFound: 해당 ID의 자녀를 찾을 수 없을 경우 발생
        NotOwnerError: 해당 자녀 정보에 접근할 권한이 없을 경우 발생

    Returns:
        ChildInfoResponse: 수정된 자녀 정보
    """

    if not child_list:
        raise ChildNotFound

    # 계정당 1명만 등록 가능하므로 첫 번째 아이 ID 사용
    child_id = child_list[0].child_id

    img_bytes = None
    if profile_img:
        img_bytes = await profile_img.read()

    update_request = ChildUpdateRequest(
        name=name,
        gender=gender,
        birth_date=birth_date,
        school=school,
        profile_img=img_bytes,  # 변환된 bytes 주입
    )

    updated_child = await update_child_service(child_id, update_request)

    if updated_child is None:
        raise ChildNotFound
    child_db = await get_child_info_service(child_id)
    if child_db is None:
        raise ChildNotFound

    child_ids = [c.child_id for c in child_list]
    if child_id not in child_ids:
        raise NotOwnerError(detail="해당 자녀 정보에 접근할 권한이 없습니다.")

    return updated_child

async def get_child_profile_img(
    child_id: Optional[int]=None,
    child_list: List[ChildInfoResponse] = Depends(get_child_list),
    get_child_profile_img_service=Depends(get_child_profile_img_service),
) -> bytes:
    """
    특정 자녀의 프로필 이미지를 가져옵니다.
    """
    if child_id is None:
        child = child_list[0]

    img_bytes = await get_child_profile_img_service(child.child_id)
    if img_bytes is None:
        raise ChildNotFound
    return img_bytes