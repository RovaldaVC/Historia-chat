# -- imports -- #
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
import enum
from datetime import datetime

# -- Schema helps to ask for user's inputs -- #

# UserCreate is made for users to add their information in sign_up.
# UserCreate asks for user's input and also validate them.
class UserCreate(BaseModel):
    name: str
    family: Optional[str] = None
    username: str = Field(..., min_length=3, max_length=32, pattern="^[a-zA-Z0-9_-]+$")
    password: str = Field(
        min_length=8,
        max_length=255,
        description="Password must be between 8 and 255 characters",
    )

# UserUpdate is made for users to add their information in sign_up.
# UserUpdate asks for user's input and also validate them.
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

# UserResponse returns user's info after user creates new account so user can see what info user used for his new account.
class UserResponse(BaseModel):
    id: int
    name: str
    family: Optional[str] = None
    username: str
    role: str
    active: bool

    model_config = ConfigDict(from_attributes=True)


# For user to insert info to create a new Private/Group Chat.
class ChatCreate(BaseModel):
    name: str

# For user to insert his info for new Message.
class MessageCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=1000)
    
# Returns all message's infos. like the sender, when the message was created and the content.
class MessageHistoryResponse(BaseModel):
    sender_id: int
    content: str
    created_at: str
    
    model_config = ConfigDict(from_attributes=True)

# returns all the Chat's Info.
class ChatListResponse(BaseModel):
    id: int
    name: str
    is_grouped:bool
    created_at: datetime
    last_message: Optional[str] = None
    last_message_time: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True) # I found out for Pydantic versian 2 we have to use it like that.

# Here we also have enum for validation. inside models.py we have enum for saving and here for validation.
class UserStatusEnum(enum.Enum):
    offline = "offline"
    online = "online"

# This Schema returns the Data of UserPresence Table.
# Frontend can use it to show the details inside UI.
class UserPresenceResponse(BaseModel):
    user_id: int
    status: UserStatusEnum
    last_seen_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)