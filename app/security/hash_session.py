import hashlib
import secrets
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from ..database.models import UserSession

def hash_session(token: str) -> str:
    return secrets.token_urlsafe(32)

def hash_session(token:str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()



def verify_session(db:Session, token:str) -> UserSession | None:
    return (
        db.query(UserSession)
        .filter(
            UserSession.token_hash == hash_session(token),
            UserSession.expires_at > datetime.now(timezone.utc),
        ).first()
    )