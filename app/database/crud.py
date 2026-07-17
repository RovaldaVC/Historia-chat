from datetime import datetime, timezone
from ..database.models import User, UserSession, Chat, ChatParticipants, Messages
from ..database.schemas import UserCreate, UserUpdate, UserResponse, ChatCreate, MessageCreate
from ..database.database import get_db
from ..security.hash_password import get_password_hash, verify_password
from ..security.authentication import create_session, COOKIE_NAME
from ..security.hash_session import hash_session
from fastapi import HTTPException, Depends, Response, Request, status
from sqlalchemy.orm import Session

def crud_get_user(user_id: int, db: Session) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return user

def crud_sign_up(user: UserCreate, db: Session) -> User:
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(status_code=422, detail="User already exists.")

    user_data = {
        "name": user.name,
        "family": user.family,
        "username": user.username,
        "password": get_password_hash(user.password),
        "role": "user",
        "active": False,
    }
    new_user = User(**user_data)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

def crud_update_user(user_id: int, user: UserUpdate, db: Session) -> User:
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found.")

    update_data = user.model_dump(exclude_unset=True)
    allowed_fields = {"name", "family", "password"}

    for field in list(update_data.keys()):
        if field not in allowed_fields:
            update_data.pop(field)

    if update_data.get("password"):
        update_data["password"] = get_password_hash(update_data["password"])

    for field, value in update_data.items():
        setattr(db_user, field, value)

    db.commit()
    db.refresh(db_user)
    return db_user

def crud_delete_user(user_id: int, db: Session) -> dict:
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found.")

    try:
        db.query(UserSession).filter(UserSession.user_id == user_id).delete()
        db.delete(db_user)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete user: {str(e)}")
    
    return {"message": "User deleted!"}

def crud_get_all_users(db: Session) -> list[User]:
    all_users = db.query(User).all()
    return all_users

def crud_login(form_data_username: str, form_data_password: str, db: Session) -> dict:
    user = db.query(User).filter(User.username == form_data_username).first()
    
    if not user or not verify_password(form_data_password, user.password): # type: ignore
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    if not user.active: # type: ignore
        raise HTTPException(status_code=403, detail="User account is not active.")
    
    session_token = create_session(db, user.id) # type: ignore
    
    return {"session_token": session_token, "user_name": user.name}

def crud_logout(response: Response, request: Request, db: Session = Depends(get_db)) -> dict:
    raw_session_token = request.cookies.get(COOKIE_NAME)
    
    if raw_session_token:
        hashed_session_token = hash_session(raw_session_token)
        db.query(UserSession).filter(UserSession.session_token == hashed_session_token).delete()
        db.commit()
    
    response.delete_cookie(COOKIE_NAME)
    return {"message": "Successfully logged out."}


def crud_create_chat(current_user_id: int, other_user_id: int, chat: ChatCreate, db: Session):
    if current_user_id == other_user_id:
        raise HTTPException(status_code=400, detail="You cannot create a private chat with yourself.") # Create Save messages later.

    existing_chat = (
        db.query(Chat)
        .join(ChatParticipants, Chat.id == ChatParticipants.chat_id)
        .filter(
            Chat.is_group.is_(False),
            ChatParticipants.user_id.in_([current_user_id, other_user_id]),
        )
        .group_by(Chat.id)
        .having(db.query(ChatParticipants).filter(ChatParticipants.chat_id == Chat.id).count() == 2)
        .first()
    )

    if existing_chat:
        return existing_chat

    new_chat = Chat(
        name=chat.name,
        is_group=False,
        created_at=datetime.now(timezone.utc),
    )
    db.add(new_chat)
    db.flush()

    for user_id in [current_user_id, other_user_id]:
        participant = ChatParticipants(
            chat_id=new_chat.id,
            user_id=user_id,
            joined_at=datetime.now(timezone.utc), # For creating Groupchat joined_at is needed, but here it's private chat! there is no need for joined_at, but for consistency, we can keep it.
        )
        db.add(participant)

    db.commit()
    db.refresh(new_chat)
    return new_chat


def crud_create_group_chat(current_user_id: int, participant_ids: list[int], group_chat: ChatCreate, db: Session):
    if not participant_ids:
        raise HTTPException(status_code=400, detail="A group chat needs at least one participant.")

    participant_ids = list(dict.fromkeys([current_user_id] + participant_ids))

    new_chat = Chat(
        name=group_chat.name,
        is_group=True,
        created_at=datetime.now(timezone.utc),
    )
    db.add(new_chat)
    db.flush()

    for user_id in participant_ids:
        participant = ChatParticipants(
            chat_id=new_chat.id,
            user_id=user_id,
            joined_at=datetime.now(timezone.utc),
        )
        db.add(participant)

    db.commit()
    db.refresh(new_chat)
    return new_chat



def crud_save_message(chat_id: int, sender_id: int, message: MessageCreate, db: Session):
    new_message = Messages(
        chat_id=chat_id,
        sender_id=sender_id,
        content=message.content,
        created_at=datetime.now(timezone.utc),
    )
    db.add(new_message)
    db.commit()
    db.refresh(new_message)
    return new_message