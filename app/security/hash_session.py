# -- Imports -- #
import hashlib
import secrets
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from ..database.models import UserSession

# We use a light weight hash so attackers can't get your raw session.
def hash_session(token:str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()

# Here we verify the hash session inside db and plain text we got as the input.
def verify_session(db:Session, token:str) -> UserSession | None:
    return (
        db.query(UserSession)
        .filter(
            UserSession.token_hash == hash_session(token),
            UserSession.expires_at > datetime.now(timezone.utc),
        ).first()
    )