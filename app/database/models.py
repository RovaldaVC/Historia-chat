# -- Imports -- #
from ..database.database import Base
from sqlalchemy import Column, ForeignKey, Integer, String, Boolean, DateTime, Enum
from sqlalchemy.orm import relationship
import enum

# Table made for all users inside our app.
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    family = Column(String(255), nullable=True, default=None)
    username = Column(String(255), nullable=False, unique=True)
    password = Column(String(512), nullable=False)
    role = Column(String(255), nullable=False, default="user")
    active = Column(Boolean, default=False)

# Table for all Sessions and cookies saved via browser.
class UserSession(Base):
    __tablename__ = "user_sessions"
    id = Column(Integer, primary_key=True, index=True)
    token_hash = Column(String(64), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    user = relationship("User")
    
# This table saves all the chats(not the messages)
class Chat(Base):
    __tablename__ = "chats"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    is_group = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False)
    
# This tables helps us Control User/Chat tables so they can share theit data and validate eachother.
class ChatParticipants(Base):
    __tablename__ = "chat_participants"
    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey("chats.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    joined_at = Column(DateTime(timezone=True), nullable=False)
    
    user = relationship("User")
    chat = relationship("Chat")

# This table saves the messages of all Chats, it has connection to Chat/ChatParticipant table.
class Messages(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey("chats.id", ondelete="CASCADE"), nullable=False)
    sender_id = Column(Integer, ForeignKey("chat_participants.id", ondelete="SET NULL"), nullable=False)
    content = Column(String(1000), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)

    chat = relationship("Chat")
    participant = relationship("ChatParticipants")
    
    
    
# This is an enum that helps us handle different status at once.
# enum means choose one option from different options
class MessageStatusEnum(enum.Enum):
    sent = "sent",
    delivered = "delivered"
    read = "read"
    
# Here the status is handles, this table connects User/Message Table and labels the chats. 
class MessageStatus(Base):
    __tablename__ = "message_status"
    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("messages.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status = Column(Enum(MessageStatusEnum), default=MessageStatusEnum.sent, nullable=False)
    
    user = relationship("User")
    messages = relationship("Messages")
    
    
# This enum handles online/offline options.
# enum means choose one option from different options
class UserStatusEnum(enum.Enum):
    offline = "offline"
    online = "online"

# This table handles if user is online or offline, also saves the last seen.
class UserPresence(Base):
    __tablename__ = "user_presence"
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    status = Column(Enum(UserStatusEnum), default=UserStatusEnum.offline, nullable=False)
    last_seen_at = Column(DateTime(timezone=True), nullable=True)
    
    user = relationship("User")
    
    
class RefreshTokens(Base):
    __tablename__ = "refresh_tokens"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    token_hash = Column(String(64), ForeignKey("user_sessions.token_hash", ondelete="CASCADE"), unique=True, index=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), ForeignKey("user_session.expires_at"), nullable=False)


    user = relationship("User")
    user_session = relationship("UserSession")