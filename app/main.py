# -- Imports -- #
from fastapi import FastAPI, Depends, HTTPException, Response, Request, WebSocket
from sqlalchemy.orm import Session
from database.database import get_db, engine, Base
from database.models import User, UserSession
from database.schemas import UserResponse, UserCreate
from database.crud import crud_get_user, crud_sign_up, crud_update_user, crud_delete_user, crud_get_all_users, crud_login, crud_logout
from fastapi.security import OAuth2PasswordRequestForm
from security.authentication import create_session, COOKIE_NAME, get_current_admin_user, get_current_user
from security.hash_password import verify_password

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
    auth_data = crud_login(form_data.username, form_data.password, db)
    
    response.set_cookie(
        key=COOKIE_NAME,
        value=auth_data["session_token"],
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax",
        max_age=7 * 24 * 60 * 60
    )
    
    return {"message": f"Welcome to Historia Chat, {auth_data['user_name']}!"}
    
@app.post("/logout")
def logout(response: Response, request: Request, db: Session = Depends(get_db)):
    return crud_logout(response, request, db)
     
@app.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id:int, db:Session = Depends(get_db), current_user:User = Depends(get_current_admin_user)):
    return crud_get_user(user_id, db)

@app.post("/users/", response_model=UserResponse)
def sign_up(user:UserCreate, db:Session = Depends(get_db)):
    return crud_sign_up(user, db)
    
@app.put("/users/me", response_model=UserResponse)
def update_user(user:UserCreate, db:Session = Depends(get_db), current_user:User = Depends(get_current_user)):
    return crud_update_user(current_user.id, user, db)
    
@app.delete("/users/{user_id}")
def delete_user(user_id:int, db:Session = Depends(get_db), current_user: User = Depends(get_current_admin_user)):
    return crud_delete_user(user_id, db)

@app.get("/users/", response_model=list[UserResponse])
def get_all_users(db:Session = Depends(get_db),
                  current_user:User = Depends(get_current_admin_user)):
    users = crud_get_all_users(db)
    return users

@app.delete("/users/me")
def delete_own_account(
    response:Response,
    db:Session = Depends(get_db),
    current_user:User = Depends(get_current_user)
):
    db.query(UserSession).filter(UserSession.user_id == current_user.id).delete()
    crud_delete_user(current_user.id, db)
    response.delete_cookie(COOKIE_NAME)
    
    return{"message": "Your account has been successfully deleted. We're sad to see you go!"}

# Webscoket here, under active development.
@app.websocket("/ws")
async def websocket_endpoint(websocket:WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Message that was: {data}")