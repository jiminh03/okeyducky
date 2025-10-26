from sqlmodel import SQLModel
from typing import Optional

class RobotInfoResponse(SQLModel):
    robot_id: int
    child_id: Optional[int] = None

    serial_number: str