import secrets
from datetime import datetime, timezone, timedelta
from fastapi import Request, HTTPException, Depends, status
from sqlalchemy.orm import Session
from ..database.database import get_db
from ..database.models import User, UserSession, ChatParticipants
from ..security.hash_session import hash_session, verify_session

SESSION_EXPIRE_DAYS = 7
COOKIE_NAME = "historia_session"

def create_session(db: Session, user_id: int) -> str:
    db.query(UserSession).filter(
        UserSession.user_id == user_id
    ).delete()
    
    raw_token = secrets.token_urlsafe(32)
    hashed_token = hash_session(raw_token)
    expires = datetime.now(timezone.utc) + timedelta(days=SESSION_EXPIRE_DAYS)
    
    new_session = UserSession(
        session_token=hashed_token,
        user_id=user_id,
        expires_at=expires
    )
    db.add(new_session)
    db.commit()
    return raw_token

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

    return participant.id # type: ignore


def get_current_admin_user(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin": # type: ignore
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to perform this action."
        )
    return current_user