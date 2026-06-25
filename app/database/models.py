from app.database.database import Base
from sqlalchemy import  Column, Integer, String, Boolean


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(25), nullable=False)
    family = Column(String(25))
    username = Column(String(100), nullable=False, unique=True)
    password = Column(String(100), nullable=False)
    active = Column(Boolean()) # Does this really work?