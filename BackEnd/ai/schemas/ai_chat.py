from pydantic import BaseModel


class ChildStartRequest(BaseModel):
    child_id: str
    text: str


class ParentStartRequest(BaseModel):
    child_id: str
    text: str
