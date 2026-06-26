from pydantic import BaseModel
from typing import Optional


class UserCreate(BaseModel):
    name : str
    family: Optional[str] #Optional doesn't work.
    username: str
    password: str
    active: bool
    
class UserResponse(UserCreate):
    id:int
    name:str
    family:Optional[str]
    username:str
    active:bool
    
    class Config:
        from_attributes = True