"""
Room Manager - Handle multi-room operations
"""
from typing import List, Optional
from sqlalchemy.orm import Session

from models import Room, User
from database import DatabaseHelper


class RoomManager:
    """Manages chat room operations"""

    @staticmethod
    def create_room(db: Session, name: str, description: str, creator_id: int, is_private: bool = False) -> Room:
        """
        Create a new chat room
        Args:
            db: Database session
            name: Room name
            description: Room description
            creator_id: User ID who creates the room
            is_private: Whether room is private
        Returns:
            Created Room object
        Raises:
            ValueError: If room name already exists
        """
        # Check if room name exists
        existing_room = db.query(Room).filter_by(name=name).first()
        if existing_room:
            raise ValueError(f"Room '{name}' already exists")

        # Create room
        room = Room(
            name=name,
            description=description,
            created_by=creator_id,
            is_private=is_private
        )
        db.add(room)
        db.commit()
        db.refresh(room)

        # Add creator as member with admin role
        creator = db.query(User).filter_by(id=creator_id).first()
        if creator:
            room.members.append(creator)
            db.commit()

        return room

    @staticmethod
    def get_room_by_id(db: Session, room_id: int) -> Optional[Room]:
        """Get room by ID"""
        return db.query(Room).filter_by(id=room_id).first()

    @staticmethod
    def get_room_by_name(db: Session, name: str) -> Optional[Room]:
        """Get room by name"""
        return db.query(Room).filter_by(name=name).first()

    @staticmethod
    def list_public_rooms(db: Session) -> List[Room]:
        """List all public rooms"""
        return db.query(Room).filter_by(is_private=False).all()

    @staticmethod
    def list_user_rooms(db: Session, user_id: int) -> List[Room]:
        """List all rooms a user is member of"""
        user = db.query(User).filter_by(id=user_id).first()
        return user.rooms if user else []

    @staticmethod
    def join_room(db: Session, user_id: int, room_id: int):
        """
        Add user to room
        Args:
            db: Database session
            user_id: User ID
            room_id: Room ID
        Raises:
            ValueError: If room not found or user already in room
        """
        room = db.query(Room).filter_by(id=room_id).first()
        if not room:
            raise ValueError("Room not found")

        user = db.query(User).filter_by(id=user_id).first()
        if not user:
            raise ValueError("User not found")

        if user in room.members:
            raise ValueError("User already in room")

        room.members.append(user)
        db.commit()

    @staticmethod
    def leave_room(db: Session, user_id: int, room_id: int):
        """
        Remove user from room
        Args:
            db: Database session
            user_id: User ID
            room_id: Room ID
        """
        room = db.query(Room).filter_by(id=room_id).first()
        if not room:
            return

        user = db.query(User).filter_by(id=user_id).first()
        if not user or user not in room.members:
            return

        room.members.remove(user)
        db.commit()

    @staticmethod
    def delete_room(db: Session, room_id: int, user_id: int):
        """
        Delete a room (only by creator)
        Args:
            db: Database session
            room_id: Room ID
            user_id: User ID (must be creator)
        Raises:
            ValueError: If room not found or user not creator
        """
        room = db.query(Room).filter_by(id=room_id).first()
        if not room:
            raise ValueError("Room not found")

        if room.created_by != user_id:
            raise ValueError("Only room creator can delete the room")

        # Don't allow deleting default room
        if room.name == "General":
            raise ValueError("Cannot delete default room")

        db.delete(room)
        db.commit()

    @staticmethod
    def get_room_members(db: Session, room_id: int) -> List[User]:
        """Get all members of a room"""
        room = db.query(Room).filter_by(id=room_id).first()
        return room.members if room else []

    @staticmethod
    def is_user_in_room(db: Session, user_id: int, room_id: int) -> bool:
        """Check if user is member of room"""
        room = db.query(Room).filter_by(id=room_id).first()
        if not room:
            return False

        user = db.query(User).filter_by(id=user_id).first()
        if not user:
            return False

        return user in room.members
