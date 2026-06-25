from database.models import User
from fastapi import HTTPException

def crud_get_user(user_id, db):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return user

def crud_post_user(user, db):
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(status_code=422, detail="User already exists.")
    
    new_user = User(**user.dict())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

def crud_update_user(user_id, user, db):
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found.")
    
    for field, value in user.dict().items():
        setattr(db_user, field, value)
    
    db.commit()
    db.refresh(db_user)
    return db_user

def crud_delete_user(user_id, db):
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found.")
    
    db.delete(db_user)
    db.commit()
    db.refresh(db_user)
    return {"message":"User deleted!"}