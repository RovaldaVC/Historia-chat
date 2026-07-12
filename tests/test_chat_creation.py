from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.crud import crud_create_chat, crud_create_group_chat
from app.database.database import Base
from app.database.models import Chat, ChatParticipants, User
from app.database.schemas import ChatCreate


def test_one_to_one_chat_is_not_created_twice():
    engine = create_engine("sqlite:///:memory:")
    TestingSessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    try:
        alice = User(
            name="Alice",
            username="alice",
            password="secret123",
            role="user",
            active=True,
        )
        bob = User(
            name="Bob",
            username="bob",
            password="secret123",
            role="user",
            active=True,
        )
        db.add_all([alice, bob])
        db.commit()
        db.refresh(alice)
        db.refresh(bob)

        first_chat = crud_create_chat(
            current_user_id=alice.id,
            other_user_id=bob.id,
            chat=ChatCreate(name="Private chat"),
            db=db,
        )
        second_chat = crud_create_chat(
            current_user_id=alice.id,
            other_user_id=bob.id,
            chat=ChatCreate(name="Private chat again"),
            db=db,
        )

        assert first_chat.id == second_chat.id
        assert db.query(Chat).count() == 1
        assert db.query(ChatParticipants).filter(ChatParticipants.chat_id == first_chat.id).count() == 2
    finally:
        db.close()


def test_group_chat_allows_multiple_participants():
    engine = create_engine("sqlite:///:memory:")
    TestingSessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    try:
        alice = User(name="Alice", username="alice2", password="secret123", role="user", active=True)
        bob = User(name="Bob", username="bob2", password="secret123", role="user", active=True)
        carol = User(name="Carol", username="carol2", password="secret123", role="user", active=True)
        db.add_all([alice, bob, carol])
        db.commit()
        db.refresh(alice)
        db.refresh(bob)
        db.refresh(carol)

        created_chat = crud_create_group_chat(
            current_user_id=alice.id,
            participant_ids=[bob.id, carol.id],
            group_chat=ChatCreate(name="Family group"),
            db=db,
        )

        assert created_chat.is_group is True
        assert db.query(ChatParticipants).filter(ChatParticipants.chat_id == created_chat.id).count() == 3
    finally:
        db.close()
