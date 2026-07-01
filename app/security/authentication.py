import secrets
from datetime import datetime, timezone, timedelta
from fastapi import Request, HTTPException, Depends, status
from sqlalchemy.orm import Session
from database.database import get_db
from database.models import User, UserSession

SESSION_EXPIRE_DAYS = 7
COOKIE_NAME = "historia_session"

def create_session(db: Session, user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    expires = datetime.now(timezone.utc) + timedelta(days=SESSION_EXPIRE_DAYS)
    
    new_session = UserSession(
        session_token=token,
        user_id=user_id,
        expires_at=expires
    )
    db.add(new_session)
    db.commit()
    return token

def get_current_user(request: Request, db: Session = Depends(get_db)):
    session_token = request.cookies.get(COOKIE_NAME)
    
    if not session_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated. Please log in."
        )

    session_record = db.query(UserSession).filter(UserSession.session_token == session_token).first()
    
    if not session_record or session_record.expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or invalid."
        )
        
    return session_record.user

def get_current_admin_user(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to perform this action."
        )
    return current_user