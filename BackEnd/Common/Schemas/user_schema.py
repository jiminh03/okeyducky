# schemas/user_schemas.py
from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict

from common.models.enums import Gender
from common.schemas.robot_schema import RobotInfoResponse

class ParentRegisterRequest(BaseModel):
    parent_name: str
    email: str
    password: str

    model_config = ConfigDict(
        from_attributes=True
    )

class LoginRequest(BaseModel):
    email: str
    password: str

class RobotLoginRequest(BaseModel):
    robot_id: int
    serial_number: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str

class TokenPayload(BaseModel):
    parent_id: int
    parent_name: str
    email: str

class RobotTokenPayload(BaseModel):
    robot_id: int
    serial_number: str

class ParentInfoResponse(BaseModel):
    parent_id: int
    parent_name: str
    email: str

    class Config:
        from_attributes = True

class ParentUpdateRequest(BaseModel):
    parent_name: Optional[str] = None
    password: Optional[str] = None

class ChildRegisterRequest(BaseModel):
    name: str
    gender: Gender
    birth_date: date
    school: Optional[str] = None
    profile_img: Optional[bytes] = None
    parent_id: int

class ChildInfoResponse(BaseModel):
    child_id: int
    name: str
    gender: Gender 
    birth_date: date
    school: Optional[str] = None
    serial_number: Optional[str] = None

    class Config:
        from_attributes = True


class ChildUpdateRequest(BaseModel):
    name: Optional[str] = None
    gender: Optional[str] = None
    birth_date: Optional[date] = None
    school: Optional[str] = None

