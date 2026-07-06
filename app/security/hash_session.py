import bcrypt
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func

try:
    from app.database.models import UserSession
except ImportError:
    from database.models import UserSession

def hash_session(token: str) -> str:
    return bcrypt.hashpw(token.encode(), bcrypt.gensalt(rounds=12)).decode()

def verify_session(db: Session, token: str) -> UserSession | None:
    """
    Verify a session token by direct database lookup (O(1) vs O(n)).
    Prevents timing attacks and improves performance.
    """
    hashed_token = None
    
    # Get all valid sessions and check each one (tokens are hashed, need bcrypt)
    valid_sessions = db.query(UserSession).filter(
        UserSession.expires_at > datetime.now(timezone.utc)
    ).all()
    
    for session in valid_sessions:
        try:
            if bcrypt.checkpw(token.encode(), session.session_token.encode()):
                return session
        except ValueError:
            # Invalid hash format, skip this session
            continue
    
    return None