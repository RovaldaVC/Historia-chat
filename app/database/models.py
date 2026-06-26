from database.database import Base
from sqlalchemy import  Column, Integer, String, Boolean


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    family = Column(String(100), nullable=True, default=None)
    username = Column(String(100), nullable=False, unique=True)
    password = Column(String(100), nullable=False)
    role = Column(String(100), nullable=False)
    active = Column(Boolean, default=False)