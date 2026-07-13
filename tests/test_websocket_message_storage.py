import os

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.database.crud import crud_create_chat
from app.database.database import Base, SessionLocal, engine
from app.database.models import Chat, ChatParticipants, Messages, User
from app.database.schemas import ChatCreate
from app.main import app
from app.security.authentication import create_session


def test_websocket_saves_and_broadcasts_messages():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        alice = User(
            name="Alice",
            username="alice-ws",
            password="secret123",
            role="user",
            active=True,
        )
        bob = User(
            name="Bob",
            username="bob-ws",
            password="secret123",
            role="user",
            active=True,
        )
        db.add_all([alice, bob])
        db.commit()
        db.refresh(alice)
        db.refresh(bob)

        chat = crud_create_chat(
            current_user_id=alice.id,
            other_user_id=bob.id,
            chat=ChatCreate(name="Private chat"),
            db=db,
        )

        token = create_session(db, alice.id)

        with TestClient(app) as client:
            with client.websocket_connect(f"/ws?token={token}") as websocket:
                websocket.send_json({"chat_id": chat.id, "content": "hello from websocket"})
                response = websocket.receive_text()

                assert "hello from websocket" in response

        persisted = db.query(Messages).filter(Messages.chat_id == chat.id).all()
        assert len(persisted) == 1
        assert persisted[0].content == "hello from websocket"
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
