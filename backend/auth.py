"""
JWT Authentication and Password Hashing
"""
import os
from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from models import User
from database import get_db

# Security configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production-please")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Password hashing functions
def hash_password(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


# JWT token functions
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token
    Args:
        data: Dictionary with user data (should include 'sub' with user ID or username)
        expires_delta: Optional custom expiration time
    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """
    Decode and verify a JWT token
    Args:
        token: JWT token string
    Returns:
        Decoded token payload or None if invalid
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def verify_token(token: str) -> Optional[str]:
    """
    Verify JWT token and return username
    Args:
        token: JWT token string
    Returns:
        Username or None if invalid
    """
    payload = decode_access_token(token)
    if payload is None:
        return None

    username: str = payload.get("sub")
    if username is None:
        return None

    return username


# Authentication functions
def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """
    Authenticate user with username and password
    Args:
        db: Database session
        username: Username
        password: Plain password
    Returns:
        User object if authentication successful, None otherwise
    """
    user = db.query(User).filter_by(username=username).first()

    if not user:
        return None

    if not user.password_hash:
        # User exists but has no password (legacy user from before auth was added)
        return None

    if not verify_password(password, user.password_hash):
        return None

    return user


def get_user_by_token(db: Session, token: str) -> Optional[User]:
    """
    Get user by JWT token
    Args:
        db: Database session
        token: JWT token
    Returns:
        User object or None
    """
    username = verify_token(token)
    if not username:
        return None

    user = db.query(User).filter_by(username=username).first()
    return user


def create_user(db: Session, username: str, password: str, email: str = None) -> User:
    """
    Create a new user
    Args:
        db: Database session
        username: Username (must be unique)
        password: Plain password (will be hashed)
        email: Optional email
    Returns:
        Created User object
    Raises:
        ValueError: If username already exists
    """
    # Check if username exists
    existing_user = db.query(User).filter_by(username=username).first()
    if existing_user:
        raise ValueError(f"Username '{username}' already exists")

    # Create new user
    password_hash = hash_password(password)
    user = User(
        username=username,
        password_hash=password_hash,
        email=email
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def update_user_last_seen(db: Session, user_id: int):
    """Update user's last_seen timestamp"""
    user = db.query(User).filter_by(id=user_id).first()
    if user:
        user.last_seen = datetime.utcnow()
        db.commit()
