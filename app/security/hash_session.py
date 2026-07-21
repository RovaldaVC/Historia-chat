# -- Imports -- #
import hashlib
from datetime import datetime, timezone
from sqlalchemy.orm import Session, joinedload
from ..database.models import UserSession

# We use a light weight hash so attackers can't get your raw session.
def hash_session(token:str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()

# Here we verify the hash session inside db and plain text we got as the input.
def verify_session(db:Session, token:str) -> UserSession | None:
    return (
        db.query(UserSession)
        .options(joinedload(UserSession.user))
        .filter(
            UserSession.token_hash == hash_session(token),
            UserSession.expires_at > datetime.now(timezone.utc),
        ).first()
    )
    
    
def delete_expired_sessions(db: Session) -> None:
    db.query(UserSession).filter(
        UserSession.expires_at < datetime.now(timezone.utc)
    ).delete()
    db.commit() # I will have to use this in some of the tasks so we won't have any expired session at all.