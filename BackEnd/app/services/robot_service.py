from app.providers.robot_providers import *

from app.exceptions import *
from app.services.child_service import *

async def register_robot(
    robot: RobotRegisterRequest,
    create_robot_service=Depends(get_create_robot_service),
    child_list: List[ChildInfoResponse] = Depends(get_child_list),
    get_child_info_service=Depends(get_child_by_id_service),
):
    child = await get_child_info_service(RobotRegisterRequest.child_id)
    if child is None:
        raise ChildNotFound
    
    child_ids = [child.id for child in child_list]
    if RobotRegisterRequest.child_id not in child_ids:
        raise NotOwnerError(detail="해당 자녀 정보에 접근할 권한이 없습니다.")
    
    return await create_robot_service(robot)

async def get_robot_info(
    serial_number: Optional[str] = None,
    child_id: Optional[int] = None,
    robot_id: Optional[int] = None,
    parents: Parent = Depends(get_current_parent),
    get_robot_by_id_service=Depends(get_robot_by_id_service),
    get_robot_by_child_id_service=Depends(get_robot_by_child_id_service),
    get_robot_by_serial_number_service=Depends(get_robot_by_serial_number_service),
):
    if robot_id:
        robot = await get_robot_by_id_service(robot_id)
    elif child_id:
         robot =  await get_robot_by_child_id_service(child_id)
    elif serial_number:
        robot = await get_robot_by_serial_number_service(serial_number)
    else:
        raise InvalidRequestError(detail="로봇 정보를 조회하기 위한 식별자가 제공되지 않았습니다.")
    
    if robot is None:
        raise RobotNotFound
    elif robot.child_id not in [child.id for child in get_child_list(parents)]:
        raise NotOwnerError(detail="해당 로봇 정보에 접근할 권한이 없습니다.")
    return robot