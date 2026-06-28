from pydantic import BaseModel
from typing import Optional


class UserCreate(BaseModel):
    name : str
    family: Optional[str] = None
    username: str
    password: str
    role: str  = "user"
    active: bool
    
class UserResponse(UserCreate):
    id:int
    name:str
    family:Optional[str]
    username:str
    active:bool
    
    class Config:
        from_attributes = True