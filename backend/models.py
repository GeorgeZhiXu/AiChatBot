"""
Database Models for AI Group Chat
Using SQLAlchemy ORM
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Table
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


# Many-to-many relationship table for room members
room_members = Table(
    'room_members',
    Base.metadata,
    Column('room_id', Integer, ForeignKey('rooms.id', ondelete='CASCADE'), primary_key=True),
    Column('user_id', Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    Column('role', String(20), default='member'),  # 'admin' or 'member'
    Column('joined_at', DateTime, default=datetime.utcnow)
)


class User(Base):
    """User model"""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=True)  # Nullable for backward compatibility
    email = Column(String(100), nullable=True)
    avatar_url = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_seen = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    created_rooms = relationship('Room', back_populates='creator', foreign_keys='Room.created_by')
    messages = relationship('Message', back_populates='user', foreign_keys='Message.user_id')
    rooms = relationship('Room', secondary=room_members, back_populates='members')

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'avatar_url': self.avatar_url,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None
        }


class Room(Base):
    """Chat room model"""
    __tablename__ = 'rooms'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_private = Column(Boolean, default=False)

    # Relationships
    creator = relationship('User', back_populates='created_rooms', foreign_keys=[created_by])
    messages = relationship('Message', back_populates='room', cascade='all, delete-orphan')
    members = relationship('User', secondary=room_members, back_populates='rooms')

    def to_dict(self, include_members=False):
        """Convert to dictionary"""
        data = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_private': self.is_private
        }
        if include_members:
            data['members'] = [m.to_dict() for m in self.members]
            data['member_count'] = len(self.members)
        return data


class Message(Base):
    """Message model"""
    __tablename__ = 'messages'

    id = Column(Integer, primary_key=True, autoincrement=True)
    room_id = Column(Integer, ForeignKey('rooms.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)  # NULL for AI messages
    content = Column(Text, nullable=False)
    is_ai = Column(Boolean, default=False, nullable=False)
    triggered_by = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)  # Who triggered AI
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    room = relationship('Room', back_populates='messages')
    user = relationship('User', back_populates='messages', foreign_keys=[user_id])
    triggered_by_user = relationship('User', foreign_keys=[triggered_by])

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'room_id': self.room_id,
            'user_id': self.user_id,
            'username': self.user.username if self.user else 'AI Assistant',
            'content': self.content,
            'is_ai': self.is_ai,
            'triggered_by': self.triggered_by,
            'timestamp': self.created_at.isoformat() if self.created_at else None
        }
