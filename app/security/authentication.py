# -- Imports -- #
import secrets
from datetime import datetime, timezone, timedelta
from fastapi import Request, HTTPException, Depends, status, WebSocket
from sqlalchemy.orm import Session
from ..database.database import get_db
from ..database.models import User, UserSession, ChatParticipants
from ..security.hash_session import hash_session, verify_session

# Token setting, expire time and cookie name.
SESSION_EXPIRE_DAYS = 7 
COOKIE_NAME = "historia_session"
MAX_SESSIONS_PER_USER = 5

# No need to use anymore. since we have the MAX_SESSION_PER_USER logic.
def revoke_all_sessions(db:Session, user_id:int) -> None:
    db.query(UserSession).filter(
        UserSession.user_id == user_id
    ).delete()

# This part is used insde crud_logout.
def delete_session(db:Session, raw_token:str) -> None:
    db.query(UserSession).filter(
        UserSession.token_hash == hash_session(raw_token)
    ).delete()
    db.commit()


# this is the core logic of creating a new session when user logs in.
def create_session(db: Session, user_id: int) -> str:
    sessions = (
        db.query(UserSession)
        .filter(UserSession.user_id == user_id)
        .order_by(UserSession.expires_at.asc())
        .all()
    )
    if len(sessions) >= MAX_SESSIONS_PER_USER:
        for old in sessions[: len(sessions) - MAX_SESSIONS_PER_USER + 1]:
            db.delete(old)
    
    
    raw_token = secrets.token_urlsafe(32)
    hashed_token = hash_session(raw_token)
    expires = datetime.now(timezone.utc) + timedelta(days=SESSION_EXPIRE_DAYS)
    
    new_session = UserSession(
        token_hash=hashed_token,
        user_id=user_id,
        expires_at=expires
    )
    db.add(new_session)
    db.commit()
    return raw_token

# here we can get the current user based on the cookie he is using inside browser.
def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    raw_token = request.cookies.get(COOKIE_NAME)
    
    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated. Please log in."
        )

    session_record = verify_session(db, raw_token)
    
    if session_record is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or invalid."
        )
    
    if not session_record.user.active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is not active."
        )
        
    return session_record.user




# by the current user logic we can get the participant id of a chat, chat_id is also needed.
# frontend will handle the chat_id. when a user clicks on a chat the chat_id will be imported inside args and then we can get it via there.
def get_current_chat_participant_id(
    chat_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> int:
    participant = (
        db.query(ChatParticipants)
        .filter(
            ChatParticipants.chat_id == chat_id,
            ChatParticipants.user_id == current_user.id,
        )
        .first()
    )

    if not participant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You are not a participant in this chat."
        )

    return participant.id

# based on get_current_user we check if the user is admin or not.
def get_current_admin_user(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to perform this action."
        )
    return current_user



# Websockets have different way of handling the get_current_user, we use websocket.cookies.get for production level rather than websocket.query_params.get because it has lower security.
def get_current_user_from_websocket(websocket: WebSocket, db: Session) -> User:
    raw_token = websocket.cookies.get(COOKIE_NAME) or websocket.query_params.get("token")
    if not raw_token:
        raise ValueError("No session token")

    session_record = verify_session(db, raw_token)
    if session_record is None or not session_record.user.active:
        raise ValueError("Invalid session")

    return session_record.user