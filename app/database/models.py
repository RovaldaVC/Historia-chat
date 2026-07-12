try:
    from app.database.database import Base
except ImportError:  # pragma: no cover - support running module directly from app dir
    from database.database import Base

from sqlalchemy import Column, ForeignKey, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship


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
    session_token = Column(String(255), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    user = relationship("User")


    
class Chats(Base):
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
    user = relationship("User"),
    chat = relationship("Chats")
    
class Messages(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey("chats.id", ondelete="CASCADE"), nullable=False)
    sender_id = Column(Integer, ForeignKey("chat_participants.id", ondelete="CASCADE"), nullable=False)
    content = Column(String(1000), nullable=False)
    created_at = Column(DateTime, nullable=False)
    chat = relationship("Chats")
    participant = relationship("ChatParticipants")