# -- Imports -- #
from fastapi import FastAPI, Depends, Response, Request, WebSocket, status
from starlette.websockets import WebSocketDisconnect
from sqlalchemy.orm import Session
import logging
import os
import json
from .database.database import get_db, engine, Base
from .database.models import User, ChatParticipants
from .database.schemas import UserResponse, UserCreate, UserUpdate, MessageCreate, ChatCreate
from .database.crud import (
    crud_get_user,
    crud_sign_up,
    crud_update_user,
    crud_delete_user,
    crud_get_all_users,
    crud_login,
    crud_logout,
    crud_save_message,
    crud_create_chat,
    crud_create_group_chat,
)
from .security.authentication import COOKIE_NAME, get_current_admin_user, get_current_user, get_current_chat_participant_id
from fastapi.security import OAuth2PasswordRequestForm
from .security.hash_session import verify_session
from .websocket.manager import manager

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
    return crud_update_user(current_user.id, user, db)
    
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
    crud_delete_user(current_user.id, db)
    response.delete_cookie(COOKIE_NAME)
    
    return {"message": "Your account has been successfully deleted. We're sad to see you go!"}

@app.post("/chats/new/private")
def create_private_chat(
    chat: ChatCreate, # later we have to use contact name instead.
    other_user_id: int, # How to get other user id? we have to set it.
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return crud_create_chat(current_user.id, other_user_id, chat, db)

@app.post("/chats/new/group")
def create_group_chat(
    chat: ChatCreate,
    participant_ids: list[int],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return crud_create_group_chat(current_user.id, participant_ids, chat, db) # type: ignore

@app.post("/chats/{chat_id}/messages")
def send_message(
    chat_id: int,
    message: MessageCreate,
    db: Session = Depends(get_db),
    sender_id: int = Depends(get_current_chat_participant_id),
) -> dict:
    return crud_save_message(chat_id, sender_id, message, db)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> None:
    token = websocket.query_params.get("token")
    chat_id_query = websocket.query_params.get("chat_id")

    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Unauthorized")
        return

    session_record = verify_session(db, token)
    if not session_record or not session_record.user.active:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid or expired session")
        return

    user_id = session_record.user_id

    await manager.connect(websocket, current_user.id)
    try:
        while True:
            raw_data = await websocket.receive_text()
            try:
                payload = json.loads(raw_data)
            except json.JSONDecodeError:
                payload = {"content": raw_data}

            if isinstance(payload, str):
                payload = {"content": payload}

            content = payload.get("content")
            if not content:
                continue

            chat_id = payload.get("chat_id") or chat_id_query
            if chat_id is None:
                await websocket.send_text("Missing chat_id")
                continue

            try:
                chat_id = int(chat_id)
            except (TypeError, ValueError):
                await websocket.send_text("Invalid chat_id")
                continue

            participant = (
                db.query(ChatParticipants)
                .filter(
                    ChatParticipants.chat_id == chat_id,
                    ChatParticipants.user_id == user_id,
                )
                .first()
            )
            if not participant:
                await websocket.send_text("You are not a participant in this chat")
                continue

            saved_message = crud_save_message(
                chat_id,
                participant.id,  # type: ignore[arg-type]
                MessageCreate(content=content),
                db,
            )
            outgoing_message = f"{session_record.user.name}: {saved_message.content}"
            await manager.send_personal_message(outgoing_message, websocket)
            await manager.broadcast(outgoing_message, sender=websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket, current_user.id)
        await manager.broadcast(f"Client #{user_id} left the chat")