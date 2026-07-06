from pydantic import BaseModel, Field
from typing import Optional


class UserCreate(BaseModel):
    name: str
    family: Optional[str] = None
    username: str
    password: str = Field(
        min_length=8,
        max_length=255,
        description="Password must be between 8 and 255 characters",
    )


class UserUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1)
    family: Optional[str] = None
    username: Optional[str] = Field(default=None, min_length=1)
    password: Optional[str] = Field(
        default=None,
        min_length=8,
        max_length=255,
        description="Password must be between 8 and 255 characters",
    )


class UserResponse(BaseModel):
    id: int
    name: str
    family: Optional[str] = None
    username: str
    role: str
    active: bool

    class Config:
        from_attributes = True