# schemas/user_schemas.py
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict

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

class LoginResponse(BaseModel):
    access_token: str

class TokenPayload(BaseModel):
    parent_id: int
    parent_name: str
    email: str

class ParentInfoResponse(BaseModel):
    user_id: int
    parent_name: str
    email: str

class ParentUpdateRequest(BaseModel):
    parent_name: Optional[str] = None
    password: Optional[str] = None

class ChildRegisterRequest(BaseModel):
    name: str
    gender: str
    birth_date: str
    school: Optional[str] = None
    parent_id: int

class ChildInfoResponse(BaseModel):
    child_id: int
    name: str

class ChildUpdateRequest(BaseModel):
    name: Optional[str] = None
    gender: Optional[str] = None
    birth_date: Optional[str] = None
    school: Optional[str] = None

