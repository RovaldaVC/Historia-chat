from datetime import datetime, timezone
from ..database.models import User, UserSession, Chat, ChatParticipants, Messages, MessageStatus, MessageStatusEnum
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
    
    hashed_token = create_session(db, user.id)
    
    return {"session_token": hashed_token, "user_name": user.name}

def crud_logout(response: Response, request: Request, db: Session = Depends(get_db)) -> dict:
    raw_session_token = request.cookies.get(COOKIE_NAME)
    
    if raw_session_token:
        hashed_session_token = hash_session(raw_session_token)
        db.query(UserSession).filter(UserSession.token_hash == hashed_session_token).delete()
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
    participants = db.query(ChatParticipants).filter(
        ChatParticipants.chat_id == chat_id
    ).all()

    participant_ids = [p.id for p in participants]

    if sender_id not in participant_ids:
        raise HTTPException(status_code=403, detail="You are not a participant of this chat room.")

    new_message = Messages(
        chat_id=chat_id,
        sender_id=sender_id,
        content=message.content,
        created_at=datetime.now(timezone.utc),
    )
    db.add(new_message)
    db.flush()

    for participant in participants:
        if participant.id != sender_id:
            msg_status = MessageStatus(
                message_id=new_message.id,
                user_id=participant.user_id,
                status=MessageStatusEnum.sent,
            )
            db.add(msg_status)

    db.commit()
    db.refresh(new_message)
    return new_message
    
    
   
def crud_get_chat_history(chat_id:int, current_user_id:int, db:Session, limit: int, offset:int = 0):
    participant = db.query(ChatParticipants).filter(
        ChatParticipants.chat_id == chat_id,
        ChatParticipants.user_id == current_user_id
    ).first()
   
    if not participant:
        raise HTTPException(status_code=403, detail="You do not have access to this chat's history.")
    
    messages = (
        db.query(Messages)
        .filter(Messages.chat_id == chat_id)
        .order_by(Messages.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    
    return messages[::-1]
   
    
def crud_update_message_status(message_id:int, current_user_id:int, new_status:MessageStatusEnum, db:Session):
    msg_status = db.query(MessageStatus).filter(
        MessageStatus.message_id == message_id,
        MessageStatus.user_id == current_user_id
    ).first()
    
    if not msg_status:
        raise HTTPException(status_code=404, detail="Message status not found or you are not a recipient.")
    
    msg_status.status = new_status
    db.commit()
    db.refresh(msg_status)
    
    return msg_status

def crud_get_user_chats(current_user: User, db:Session):
    user_chats = (
        db.query(Chat)
        .join(ChatParticipants, Chat.id == ChatParticipants.chat_id)
        .filter(ChatParticipants.user_id == current_user.id)
        .all()
    )
    
    chat_summaries = []
    
    for chat in user_chats:
        last_msg = (
            db.query(Messages)
            .filter(Messages.chat_id == chat.id)
            .order_by(Messages.created_at.desc())
            .first()
        )
        
        chat_summaries.append({
            "id": chat.id,
            "name": chat.name,
            "is_group": chat.is_group,
            "created_at": chat.created_at,
            "last_message": last_msg.content if last_msg else None,
            "last_message_time": last_msg.created_at if last_msg else None
        })
        
        chat_summaries.sort(
            key=lambda x: x["last_message_time"] or x["created_at"], 
            reverse=True
        )
        
        return chat_summaries
    
    
def crud_get_chat_history(chat_id:int, user_id:int, db:Session, limit:int=50, offset: int = 0):
    messages = (
        db.query(Messages)
        .filter(Messages.chat_id == chat_id)
        .order_by(Messages.created_at.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )
    for msg in messages:
        return[
            {
                "sender_id": msg.sender,
                "content": msg.content,
                "created_at": msg.created_at.isoformat()
            }
        ]