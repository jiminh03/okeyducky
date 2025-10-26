# schemas/child_schemas.py
from sqlmodel import SQLModel
from datetime import date
from typing import Optional
from .robot_schemas import RobotInfoResponse # robot_schemas.py 필요
from Repo.Models.enums import Gender

class ChildRegisterRequest(SQLModel):
    name: str
    gender: Gender 
    birth_date: date
    school: Optional[str] = None
    serial_number: str

class ChildInfoResponse(SQLModel):
    child_id: int
    name: str
    gender: Gender 
    birth_date: date
    school: Optional[str] = None
    robot: Optional[RobotInfoResponse] = None # Robot 스키마 포함

class ChildUpdateRequest(SQLModel):
    name: Optional[str] = None
    gender: Optional[Gender] = None 
    birth_date: Optional[date] = None
    school: Optional[str] = None