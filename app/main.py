# -- Imports -- #
from fastapi import FastAPI, Depends, HTTPException, Response, Request
from sqlalchemy.orm import Session
from database.database import get_db, engine, Base
from database.models import User, UserSession
from database.schemas import UserResponse, UserCreate
from database.crud import crud_get_user, crud_post_user, crud_update_user, crud_delete_user, crud_get_all_users
from fastapi.security import OAuth2PasswordRequestForm
from security.authentication import create_session, COOKIE_NAME, get_current_admin_user

# -- Main Engine -- #
Base.metadata.create_all(bind=engine)
app = FastAPI()

# -- Routes -- #
@app.post("/login")
def login(
    response: Response, 
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or user.password != form_data.password:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    session_token = create_session(db, user.id)
    response.set_cookie(
        key=COOKIE_NAME,
        value=session_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=7 * 24 * 60 * 60
    )
    return {"message": f"Welcome to Historia Chat, {user.name}!"}
    
@app.post("/logout")
def logout(response: Response, request: Request, db: Session = Depends(get_db)):
    session_token = request.cookies.get(COOKIE_NAME)
    
    if session_token:
        db.query(UserSession).filter(UserSession.session_token == session_token).delete()
        db.commit()
    
    response.delete_cookie(COOKIE_NAME)
    return {"message": "Successfully logged out."}
     
@app.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id:int, db:Session = Depends(get_db)):
    return crud_get_user(user_id, db)

@app.post("/users/", response_model=UserResponse)
def create_user(user:UserCreate, db:Session = Depends(get_db)):
    return crud_post_user(user, db)
    
@app.put("/users/{user_id}", response_model=UserResponse)
def update_user(user_id:int, user:UserCreate, db:Session = Depends(get_db)):
    return crud_update_user(user_id, user, db)
    
@app.delete("/users/{user_id}")
def delete_user(user_id:int, db:Session = Depends(get_db)):
    return crud_delete_user(user_id, db) 
# This must be for admins.
# we have to create one for users to delete their account.

@app.get("/users/", response_model=list[UserResponse])
def get_all_users(db:Session = Depends(get_db),
                  current_user:User = Depends(get_current_admin_user)):
    users = crud_get_all_users(db)
    return users