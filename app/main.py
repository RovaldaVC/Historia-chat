# -- Imports -- #
from fastapi import FastAPI, Depends, Response, Request, WebSocket, status
from starlette.websockets import WebSocketDisconnect
from sqlalchemy.orm import Session
import logging
import os
from .database.database import get_db, engine, Base
from .database.models import User, UserSession
from .database.schemas import UserResponse, UserCreate, UserUpdate
from .database.crud import crud_get_user, crud_sign_up, crud_update_user, crud_delete_user, crud_get_all_users, crud_login, crud_logout
from .security.authentication import COOKIE_NAME, get_current_admin_user, get_current_user
from fastapi.security import OAuth2PasswordRequestForm
from .security.hash_session import verify_session
from websocket.manager import manager

logger = logging.getLogger(__name__)

# -- Main Engine -- #
try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    logger.error(f"Failed to initialize database: {e}")
    raise
app = FastAPI()

# -- Routes -- #
@app.post("/login")
def login(
    response: Response, 
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(get_db)
) -> dict:
    auth_data = crud_login(form_data.username, form_data.password, db)
    
    response.set_cookie(
        key=COOKIE_NAME,
        value=auth_data["session_token"],
        httponly=True,
        secure=os.getenv("SECURE_COOKIES", "true").lower() == "true",
        samesite="lax",
        max_age=7 * 24 * 60 * 60
    )
    
    return {"message": f"Welcome to Historia Chat, {auth_data['user_name']}!"}
    
@app.post("/logout")
def logout(response: Response, request: Request, db: Session = Depends(get_db)) -> dict:
    return crud_logout(response, request, db)
     
@app.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_admin_user)) -> User:
    return crud_get_user(user_id, db)

@app.post("/users/", response_model=UserResponse)
def sign_up(user: UserCreate, db: Session = Depends(get_db)) -> User:
    return crud_sign_up(user, db)
    
@app.put("/users/me", response_model=UserResponse)
def update_user(user: UserUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> UserResponse:
    return crud_update_user(current_user.id, user, db) # type: ignore
    
@app.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_admin_user)) -> dict:
    return crud_delete_user(user_id, db)

@app.get("/users/", response_model=list[UserResponse])
def get_all_users(db: Session = Depends(get_db), current_user: User = Depends(get_current_admin_user)) -> list[User]:
    users = crud_get_all_users(db)
    return users

@app.delete("/users/me")
def delete_own_account(
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> dict:
    crud_delete_user(current_user.id, db) # type: ignore
    response.delete_cookie(COOKIE_NAME)
    
    return {"message": "Your account has been successfully deleted. We're sad to see you go!"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, db: Session = Depends(get_db)) -> None:
    token = websocket.query_params.get("token")
    
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Unauthorized")
        return
    
    session_record = verify_session(db, token)
    if not session_record or not session_record.user.active:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid or expired session")
        return
    
    user_id = session_record.user_id
    
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.send_personal_message(f"You wrote: {data}", websocket)
            await manager.broadcast(f"Client #{user_id} says: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"Client #{user_id} left the chat")