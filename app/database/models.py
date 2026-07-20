from ..database.database import Base
from sqlalchemy import Column, ForeignKey, Integer, String, Boolean, DateTime, Enum
from sqlalchemy.orm import relationship
import enum

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    family = Column(String(255), nullable=True, default=None)
    username = Column(String(255), nullable=False, unique=True)
    password = Column(String(512), nullable=False)
    role = Column(String(255), nullable=False, default="user")
    active = Column(Boolean, default=False)


class UserSession(Base):
    __tablename__ = "user_sessions"
    id = Column(Integer, primary_key=True, index=True)
    token_hash = Column(String(64), unique=True, index=True, nullable=False) # I'm removing bcrypt.
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    user = relationship("User")
    
class Chat(Base):
    __tablename__ = "chats"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    is_group = Column(Boolean, default=False)
    created_at = Column(DateTime, nullable=False)
    

class ChatParticipants(Base):
    __tablename__ = "chat_participants"
    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey("chats.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    joined_at = Column(DateTime, nullable=False)
    
    user = relationship("User")
    chat = relationship("Chat")


class Messages(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey("chats.id", ondelete="CASCADE"), nullable=False)
    sender_id = Column(Integer, ForeignKey("chat_participants.id", ondelete="SET NULL"), nullable=False)
    content = Column(String(1000), nullable=False)
    created_at = Column(DateTime, nullable=False)

    chat = relationship("Chat")
    participant = relationship("ChatParticipants")
    
    
    
    
class MessageStatusEnum(enum.Enum):
    sent = "sent",
    delivered = "delivered"
    read = "read"
class MessageStatus(Base):
    __tablename__ = "message_status"
    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("messages.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status = Column(Enum(MessageStatusEnum), default=MessageStatusEnum.sent, nullable=False)
    
    user = relationship("User")
    messages = relationship("Messages")
    
    

class UserStatusEnum(enum.Enum):
    offline = "offline"
    online = "online"
class UserPresence(Base):
    __tablename__ = "user_presence"
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    status = Column(Enum(UserStatusEnum), default=UserStatusEnum.offline, nullable=False)
    last_seen_at = Column(DateTime, nullable=True)