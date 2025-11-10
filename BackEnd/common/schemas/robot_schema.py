from sqlmodel import SQLModel
from typing import Optional

class RobotRegisterRequest(SQLModel):
    serial_number: str
    child_id: Optional[int] = None


class RobotInfoResponse(SQLModel):
    robot_id: int
    child_id: Optional[int] = None

    serial_number: str