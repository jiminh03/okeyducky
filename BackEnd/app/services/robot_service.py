from app.providers.robot_providers import *

from app.exceptions import *
from app.services.child_service import *


async def register_robot(
    robot: RobotRegisterRequest,
    create_robot_service=Depends(get_create_robot_service),
    child_list: List[ChildInfoResponse] = Depends(get_child_list),
    get_child_info_service=Depends(get_child_by_id_service),
) -> RobotInfoResponse:
    """
    로봇을 등록합니다.

    Args:
        robot (RobotRegisterRequest): 로봇 등록 요청 데이터
        create_robot_service (Depends, optional): 로봇 생성 서비스. Defaults to Depends(get_create_robot_service).
        child_list (List[ChildInfoResponse], optional): 현재 로그인한 부모님의 자녀 목록. Defaults to Depends(get_child_list).
        get_child_info_service (Depends, optional): ID로 자녀 정보를 가져오는 서비스. Defaults to Depends(get_child_by_id_service).

    Raises:
        ChildNotFound: 해당 ID의 자녀를 찾을 수 없을 경우 발생
        NotOwnerError: 해당 자녀 정보에 접근할 권한이 없을 경우 발생

    Returns:
        RobotInfoResponse: 등록된 로봇 정보
    """
    child = await get_child_info_service(robot.child_id)
    if child is None:
        raise ChildNotFound

    child_ids = [child.child_id for child in child_list]
    if robot.child_id not in child_ids:
        raise NotOwnerError(detail="해당 자녀 정보에 접근할 권한이 없습니다.")

    return await create_robot_service(robot)


async def get_robot_info(
    serial_number: Optional[str] = None,
    child_id: Optional[int] = None,
    robot_id: Optional[int] = None,
    get_robot_by_id_service=Depends(get_robot_by_id_service),
    get_robot_by_child_id_service=Depends(get_robot_by_child_id_service),
    get_robot_by_serial_number_service=Depends(get_robot_by_serial_number_service),
    child_list: List[ChildInfoResponse] = Depends(get_child_list),
) -> RobotInfoResponse:
    """
    로봇 정보를 가져옵니다.

    Args:
        serial_number (Optional[str], optional): 시리얼 번호. Defaults to None.
        child_id (Optional[int], optional): 자녀 ID. Defaults to None.
        robot_id (Optional[int], optional): 로봇 ID. Defaults to None.
        get_robot_by_id_service (Depends, optional): ID로 로봇 정보를 가져오는 서비스. Defaults to Depends(get_robot_by_id_service).
        get_robot_by_child_id_service (Depends, optional): 자녀 ID로 로봇 정보를 가져오는 서비스. Defaults to Depends(get_robot_by_child_id_service).
        get_robot_by_serial_number_service (Depends, optional): 시리얼 번호로 로봇 정보를 가져오는 서비스. Defaults to Depends(get_robot_by_serial_number_service).
        child_list (List[ChildInfoResponse], optional): 현재 로그인한 부모님의 자녀 목록. Defaults to Depends(get_child_list).

    Raises:
        InvalidRequestError: 로봇 정보를 조회하기 위한 식별자가 제공되지 않았을 경우 발생
        RobotNotFound: 해당 로봇을 찾을 수 없을 경우 발생
        NotOwnerError: 해당 로봇 정보에 접근할 권한이 없을 경우 발생

    Returns:
        RobotInfoResponse: 로봇 정보
    """
    if robot_id:
        robot = await get_robot_by_id_service(robot_id)
    elif child_id:
        robot = await get_robot_by_child_id_service(child_id)
    elif serial_number:
        robot = await get_robot_by_serial_number_service(serial_number)
    else:
        raise InvalidRequestError(
            detail="로봇 정보를 조회하기 위한 식별자가 제공되지 않았습니다."
        )

    if robot is None:
        raise RobotNotFound
    elif robot.child_id not in [child.child_id for child in child_list]:
        raise NotOwnerError(detail="해당 로봇 정보에 접근할 권한이 없습니다.")
    return robot