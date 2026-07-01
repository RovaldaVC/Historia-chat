import bcrypt
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from database.models import UserSession

def hash_session(token: str) -> str:
    return bcrypt.hashpw(token.encode(), bcrypt.gensalt()).decode()

def verify_session(db: Session, token: str) -> UserSession | None:
    sessions = db.query(UserSession).filter(
        UserSession.expires_at > datetime.now(timezone.utc)
    ).all()
    for session in sessions:
        if bcrypt.checkpw(token.encode(), session.session_token.encode()):
            return session
    return None