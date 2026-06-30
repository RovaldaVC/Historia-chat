from database.models import User, UserSession
from fastapi import HTTPException, Depends, Response, Request
from fastapi.security import OAuth2PasswordRequestForm
from database.schemas import UserCreate
from sqlalchemy.orm import Session
from database.database import get_db
from security.hash_password import get_password_hash, verify_password
from security.authentication import create_session, COOKIE_NAME

def crud_get_user(user_id:int, db:Session):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return user

def crud_sign_up(user:UserCreate, db:Session):
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(status_code=422, detail="User already exists.")
    
    user_data = {
        "name": user.name,
        "family": user.family,
        "username":user.username,
        "password":get_password_hash(user.password),
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
    
    update_data = user.model_dump()
    
    if "password" in update_data and update_data["password"]:
        update_data["password"] = get_password_hash(update_data["password"])
    
    for field, value in update_data.items():
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

def crud_login(form_data_username: str, form_data_password: str, db: Session):
    user = db.query(User).filter(User.username == form_data_username).first()
    
    if not user or not verify_password(form_data_password, user.password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
        
    session_token = create_session(db, user.id)
    
    return {"session_token": session_token, "user_name": user.name}

def crud_logout(response: Response, request: Request, db: Session = Depends(get_db)):
    session_token = request.cookies.get(COOKIE_NAME)
    
    if session_token:
        db.query(UserSession).filter(UserSession.session_token == session_token).delete()
        db.commit()
    
    response.delete_cookie(COOKIE_NAME)
    return {"message": "Successfully logged out."}