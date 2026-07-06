from pydantic import BaseModel, Field
from typing import Optional


class UserCreate(BaseModel):
    name : str
    family: Optional[str] = None
    username: str
    password: str = Field(
        min_length=8,
        max_length=255,
        description= "Password must be between 8 and 255 characters"
    )
    role: str  = "user"
class UserUpdate(BaseModel):
    name : str
    family: Optional[str] = None
    username: str
    password: str = Field(
        min_length=8,
        max_length=255,
        description= "Password must be between 8 and 255 characters"
    )
    
class UserResponse(UserCreate):
    id:int
    name:str
    family:Optional[str]
    username:str
    active:bool
    
    class Config:
        from_attributes = True