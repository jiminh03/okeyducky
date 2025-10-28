from app.providers.robot_providers import *

async def register_robot(
    robot: RobotRegisterRequest,
    create_robot_service=Depends(get_create_robot_service),
):
    return await create_robot_service(robot)

async def get_robot_info(
    serial_number: Optional[str] = None,
    child_id: Optional[int] = None,
    robot_id: Optional[int] = None,
    get_robot_by_id_service=Depends(get_robot_by_id_service),
    get_robot_by_child_id_service=Depends(get_robot_by_child_id_service),
    get_robot_by_serial_number_service=Depends(get_robot_by_serial_number_service),
):
    if robot_id:
        return await get_robot_by_id_service(robot_id)
    elif child_id:
        return await get_robot_by_child_id_service(child_id)
    elif serial_number:
        return await get_robot_by_serial_number_service(serial_number)
    else:
        raise InvalidRobotError