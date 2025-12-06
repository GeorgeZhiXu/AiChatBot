"""
Database connection and session management
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager

from models import Base, User, Room, Message

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./chat.db')

# Create engine
# For SQLite, we use StaticPool to allow same-thread access
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if 'sqlite' in DATABASE_URL else {},
    poolclass=StaticPool if 'sqlite' in DATABASE_URL else None,
    echo=False  # Set to True for SQL debug logging
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize database - create all tables"""
    print("[Database] Creating tables...")
    Base.metadata.create_all(bind=engine)

    # Create default room if not exists
    db = SessionLocal()
    try:
        default_room = db.query(Room).filter_by(name="General").first()
        if not default_room:
            default_room = Room(
                name="General",
                description="Default chat room for everyone",
                is_private=False
            )
            db.add(default_room)
            db.commit()
            print("[Database] Created default 'General' room")
    except Exception as e:
        print(f"[Database] Error creating default room: {e}")
        db.rollback()
    finally:
        db.close()

    print("[Database] Database initialized successfully")


@contextmanager
def get_db() -> Session:
    """
    Get database session with context manager
    Usage:
        with get_db() as db:
            user = db.query(User).first()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_session() -> Session:
    """Get database session (for dependency injection)"""
    return SessionLocal()


# Database helper functions
class DatabaseHelper:
    """Helper functions for common database operations"""

    @staticmethod
    def get_or_create_user(db: Session, username: str, password_hash: str = None) -> User:
        """Get existing user or create new one"""
        user = db.query(User).filter_by(username=username).first()
        if not user:
            user = User(username=username, password_hash=password_hash)
            db.add(user)
            db.commit()
            db.refresh(user)
        return user

    @staticmethod
    def get_room_by_id(db: Session, room_id: int) -> Room:
        """Get room by ID"""
        return db.query(Room).filter_by(id=room_id).first()

    @staticmethod
    def get_default_room(db: Session) -> Room:
        """Get default 'General' room"""
        return db.query(Room).filter_by(name="General").first()

    @staticmethod
    def add_message(db: Session, room_id: int, user_id: int, content: str, is_ai: bool = False, triggered_by: int = None) -> Message:
        """Add a new message"""
        message = Message(
            room_id=room_id,
            user_id=user_id,
            content=content,
            is_ai=is_ai,
            triggered_by=triggered_by
        )
        db.add(message)
        db.commit()
        db.refresh(message)
        return message

    @staticmethod
    def get_recent_messages(db: Session, room_id: int, limit: int = 50) -> list[Message]:
        """Get recent messages from a room"""
        return db.query(Message)\
            .filter_by(room_id=room_id)\
            .order_by(Message.created_at.desc())\
            .limit(limit)\
            .all()[::-1]  # Reverse to get oldest first

    @staticmethod
    def add_user_to_room(db: Session, user_id: int, room_id: int, role: str = 'member'):
        """Add user to room"""
        room = db.query(Room).filter_by(id=room_id).first()
        user = db.query(User).filter_by(id=user_id).first()
        if room and user and user not in room.members:
            room.members.append(user)
            db.commit()

    @staticmethod
    def remove_user_from_room(db: Session, user_id: int, room_id: int):
        """Remove user from room"""
        room = db.query(Room).filter_by(id=room_id).first()
        user = db.query(User).filter_by(id=user_id).first()
        if room and user and user in room.members:
            room.members.remove(user)
            db.commit()

    @staticmethod
    def get_user_rooms(db: Session, user_id: int) -> list[Room]:
        """Get all rooms a user is member of"""
        user = db.query(User).filter_by(id=user_id).first()
        return user.rooms if user else []
