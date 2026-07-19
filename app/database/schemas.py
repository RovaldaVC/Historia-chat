from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
import enum
from datetime import datetime

class UserCreate(BaseModel):
    name: str
    family: Optional[str] = None
    username: str = Field(..., min_length=3, max_length=32, pattern="^[a-zA-Z0-9_-]+$")
    password: str = Field(
        min_length=8,
        max_length=255,
        description="Password must be between 8 and 255 characters",
    )


class UserUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1)
    family: Optional[str] = None
    username: Optional[str] = Field(default=None, min_length=3, max_length=32, pattern="^[a-zA-Z0-9_-]+$")
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
        
        
        
class ChatCreate(BaseModel):
    name: str
    
class MessageCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=1000)
    

class MessageHistoryResponse(BaseModel):
    sender_id: int
    content: str
    created_at: str
    
    class Config:
        from_attributes = True

class ChatList(BaseModel):
    name: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserStatusEnum(enum.Enum):
    offline = "offline"
    online = "online"
class UserPresenceResponse(BaseModel):
    user_id: int
    status: UserStatusEnum
    last_seen_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True