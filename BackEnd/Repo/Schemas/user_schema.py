# schemas/user_schemas.py
from typing import Optional
from sqlmodel import SQLModel

# Base 모델은 SQLModel 상속 없이 생성 가능 (Pydantic 처럼)
# 또는 SQLModel을 상속하여 DB 모델과 필드를 공유할 수도 있음
class ParentRegisterRequest(SQLModel):
    parent_name: str
    email: str
    password: str

class LoginRequest(SQLModel):
    email: str
    password: str

class LoginResponse(SQLModel):
    access_token: str

class ParentInfoResponse(SQLModel):
    user_id: int
    parent_name: str
    email: str

class ParentUpdateRequest(SQLModel):
    parent_name: Optional[str] = None
    password: Optional[str] = None

