from pydantic import BaseModel
from datetime import date
from typing import Optional
from common.schemas.robot_schema import RobotInfoResponse # robot_schemas.py 필요
from common.models.enums import Gender

class ChildRegisterRequest(BaseModel):
    name: str
    gender: Gender 
    birth_date: date
    school: Optional[str] = None
    serial_number: str

class ChildInfoResponse(BaseModel):
    child_id: int
    name: str
    gender: Gender 
    birth_date: date
    school: Optional[str] = None
    robot: Optional[RobotInfoResponse] = None # Robot 스키마 포함

class ChildUpdateRequest(BaseModel):
    name: Optional[str] = None
    gender: Optional[Gender] = None 
    birth_date: Optional[date] = None
    school: Optional[str] = None