# -- Imports -- #
from datetime import datetime, timezone
from ..database.models import User, UserSession, Chat, ChatParticipants, Messages, MessageStatus, MessageStatusEnum
from ..database.schemas import UserCreate, UserUpdate, ChatCreate, MessageCreate
from ..database.database import get_db
from ..security.hash_password import get_password_hash, verify_password
from ..security.authentication import create_session, COOKIE_NAME, delete_session, verify_session, create_refresh_token
from fastapi import HTTPException, Depends, Response, Request
from sqlalchemy.orm import Session

# -- Here we can see all the endpoint logic's inside main.py -- #

# Here we can get user based on their id.
def crud_get_user(user_id: int, db: Session) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return user

# This is the signup logic behind the endpoint.
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

# Logic for updating user
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

# Logic of deleting a user, if you are admin you can delete other peoples' account, if not you can only delete your own!
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

# Only admins have access to that. They can get all users at once.
def crud_get_all_users(db: Session) -> list[User]:
    all_users = db.query(User).all()
    return all_users

# Core logic of loggin in to your account.
def crud_login(form_data_username: str, form_data_password: str, db: Session) -> dict:
    user = db.query(User).filter(User.username == form_data_username).first()
    
    if not user or not verify_password(form_data_password, user.password): # type: ignore
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    if not user.active: # type: ignore
        raise HTTPException(status_code=403, detail="User account is not active.")
    
    hashed_token = create_session(db, user.id)
    
    return {"session_token": hashed_token, "user_name": user.name}

# Core logic of logging out of your account, cookie will be removed after that.
def crud_logout(response: Response, request: Request, db: Session = Depends(get_db)) -> dict:
    raw_session_token = request.cookies.get(COOKIE_NAME)
    
    if raw_session_token:
        delete_session(db, raw_session_token)
        
    response.delete_cookie(COOKIE_NAME)
    return {"message": "Successfully logged out."}

# This is the logic of creating a new private chat.
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

# This is the logic of creating a new group chat.
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


# this logic saves all the messages you make, also saves them inside participant for relationship situations.
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
    
    
# All the messsage history of a chat can be restored based on this logic, messages will be shown by limit = 50 for performance issues.
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
   
# status message will be updated, it might be sent, delivered or read.
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

# Here we have the core logic of getting all chats of the current user. user can see all of his chat's.
# each chat also shows last message and last message time.
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
    
# This is the logic for getting all the messages inside a chat.
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
        

def crud_refresh_session(raw_refresh_token: str, db: Session) -> dict:
    token_record = verify_session(db, raw_refresh_token)
    if token_record is None:
        raise HTTPException(status_code=401, detail="Refresh token expired or invalid.")

    new_session_token = create_session(db, token_record.user_id)
    return {"session_token": new_session_token} # This refresh_session should use something else instead of verify_session; a new one that can find out expire time is near, so it creates a new session and then deletes the old one when user dissconects from websocket! i have to check it inside websocket when user gets online. So for now this doesn't work at all and is not ready.


# Later we can lable all the cruds by saving them inside different classes
# For example class Crud User_web_work and inside it functions won't have crud as their name anymore, then we have to fix the imports too.