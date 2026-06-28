from database.models import User
from fastapi import HTTPException, Depends
from database.schemas import UserCreate
from sqlalchemy.orm import Session
from database.database import get_db


def crud_get_user(user_id:int, db:Session):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return user

def crud_post_user(user:UserCreate, db:Session):
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(status_code=422, detail="User already exists.")
    
    user_data = {
        "name": user.name,
        "family": user.family,
        "username":user.username,
        "password":user.password,
        "role":"user"
    }
    new_user = User(**user_data)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

def crud_update_user(user_id:int, user:UserCreate, db:Session):
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found.")
    
    for field, value in user.dict().items():
        setattr(db_user, field, value)
    
    db.commit()
    db.refresh(db_user)
    return db_user

def crud_delete_user(user_id:int, db:Session):
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found.")
    
    db.delete(db_user)
    db.commit()
    return {"message":"User deleted!"}

def crud_get_all_users(db:Session):
    all_users = db.query(User).all()
    return all_users