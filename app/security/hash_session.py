import bcrypt
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database.models import UserSession

def hash_session(token: str) -> str:
    return bcrypt.hashpw(token.encode(), bcrypt.gensalt(rounds=12)).decode()

def verify_session(db: Session, token: str) -> UserSession | None:
    valid_sessions = db.query(UserSession).filter(
        UserSession.expires_at > datetime.now(timezone.utc)
    ).all()
    
    for session in valid_sessions:
        try:
            if bcrypt.checkpw(token.encode(), session.session_token.encode()):
                return session
        except ValueError:
            continue
    return None