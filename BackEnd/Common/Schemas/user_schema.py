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

class ParentInfoResponse(BaseModel):
    user_id: int
    parent_name: str
    email: str

class ParentUpdateRequest(BaseModel):
    parent_name: Optional[str] = None
    password: Optional[str] = None

