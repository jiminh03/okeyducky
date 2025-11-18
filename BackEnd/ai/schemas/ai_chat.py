from pydantic import BaseModel

from common.schemas.dialogue_schema import DialogueLogBase

class ChildStartRequest(DialogueLogBase):
    child_id: str

class ParentStartRequest(DialogueLogBase):
    child_id: str
