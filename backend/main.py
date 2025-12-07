"""
AI Group Chat Backend
Real-time group chat with AI assistant (@AI trigger)
Built with FastAPI + Socket.IO + DeepSeek AI + SQLite
"""
import os
import re
import asyncio
from datetime import datetime
from dataclasses import dataclass
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import socketio

from deepseek_client import chat_completion_stream
from database import init_db, get_db, DatabaseHelper
from models import User as DBUser, Room as DBRoom, Message as DBMessage
from auth import create_access_token, authenticate_user, create_user, get_user_by_token
from room_manager import RoomManager
from fastapi import HTTPException, Header
from pydantic import BaseModel


# ========== FastAPI Application ==========
app = FastAPI(title="AI Group Chat API")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ========== Socket.IO Server ==========
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    logger=True,
    engineio_logger=False  # Reduce log noise
)


# ========== Data Models ==========
@dataclass
class User:
    """User in the chat room"""
    sid: str  # Socket.IO session ID
    username: str
    joined_at: datetime


@dataclass
class ChatMessage:
    """Chat message model"""
    id: str
    username: str
    content: str
    timestamp: datetime
    is_ai: bool = False

    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'username': self.username,
            'content': self.content,
            'timestamp': self.timestamp.isoformat(),
            'is_ai': self.is_ai
        }


# ========== State Management ==========
class ChatState:
    """Global chat state manager with database integration"""
    def __init__(self):
        self.users: Dict[str, User] = {}  # sid -> User (online users)
        self.user_db_ids: Dict[str, int] = {}  # sid -> user_id in database
        self.user_current_rooms: Dict[str, int] = {}  # sid -> current_room_id
        self.ai_queue: asyncio.Queue = asyncio.Queue()
        self.ai_processing: bool = False
        self.default_room_id: int = None  # Will be set on startup

    def add_user(self, sid: str, username: str, user_db_id: int):
        """Add a user to the chat"""
        self.users[sid] = User(sid, username, datetime.now())
        self.user_db_ids[sid] = user_db_id

    def remove_user(self, sid: str) -> Optional[str]:
        """Remove a user and return their username"""
        user = self.users.pop(sid, None)
        self.user_db_ids.pop(sid, None)
        self.user_current_rooms.pop(sid, None)
        return user.username if user else None

    def get_username(self, sid: str) -> Optional[str]:
        """Get username by socket ID"""
        user = self.users.get(sid)
        return user.username if user else None

    def get_user_db_id(self, sid: str) -> Optional[int]:
        """Get database user ID by socket ID"""
        return self.user_db_ids.get(sid)

    def set_user_room(self, sid: str, room_id: int):
        """Set user's current room"""
        self.user_current_rooms[sid] = room_id

    def get_user_room(self, sid: str) -> Optional[int]:
        """Get user's current room ID"""
        return self.user_current_rooms.get(sid)

    def username_exists(self, username: str) -> bool:
        """Check if username already taken (in current online users)"""
        return any(u.username == username for u in self.users.values())

    def get_context_for_ai(self, room_id: int, max_messages: int = 10) -> List[Dict[str, str]]:
        """Get recent chat context for AI from database"""
        with get_db() as db:
            messages = DatabaseHelper.get_recent_messages(
                db,
                room_id,
                limit=max_messages
            )
            result = []
            for msg in messages:
                role = "assistant" if msg.is_ai else "user"
                content = msg.content if msg.is_ai else f"[{msg.user.username if msg.user else 'Unknown'}]: {msg.content}"
                result.append({"role": role, "content": content})
            return result


# Global state instance
chat_state = ChatState()

# Thread pool for blocking AI calls
executor = ThreadPoolExecutor(max_workers=2)


# ========== @AI Detection ==========
def detect_ai_mention(message: str) -> bool:
    """Detect if message contains @AI mention"""
    # Match @AI or @ai with optional spaces, regardless of what follows
    patterns = [
        r'@\s*AI',
        r'@\s*ai'
    ]
    return any(re.search(pattern, message, re.IGNORECASE) for pattern in patterns)


def extract_ai_query(message: str) -> str:
    """Extract actual query from @AI message"""
    # Remove @AI mention (with optional spaces before AI)
    cleaned = re.sub(r'@\s*AI', '', message, flags=re.IGNORECASE).strip()
    return cleaned if cleaned else message


# ========== AI Processing ==========
async def process_ai_queue():
    """Background task to process AI requests from queue"""
    print("[AI Queue] Started processing AI requests")

    while True:
        try:
            # Get request from queue
            request = await chat_state.ai_queue.get()

            # Check if AI is already processing
            if chat_state.ai_processing:
                await sio.emit('ai_busy', {
                    'message': 'AI is currently processing another request. Please wait...'
                })
                # Put request back to queue
                await chat_state.ai_queue.put(request)
                await asyncio.sleep(2)
                continue

            # Process the request
            chat_state.ai_processing = True
            try:
                await handle_ai_request(request)
            except Exception as e:
                print(f"[AI Error] {e}")
                await sio.emit('ai_error', {
                    'message': f'AI processing failed: {str(e)}'
                })
            finally:
                chat_state.ai_processing = False
                chat_state.ai_queue.task_done()

        except Exception as e:
            print(f"[AI Queue Error] {e}")
            await asyncio.sleep(1)


async def handle_ai_request(request: dict):
    """Handle a single AI request with streaming"""
    query = request['query']
    username = request['username']
    user_db_id = request['user_db_id']
    room_id = request['room_id']
    timestamp = request['timestamp']

    print(f"[AI] Processing request from {username} in room {room_id}: {query[:50]}...")

    # Build message context from current room
    context = chat_state.get_context_for_ai(room_id, max_messages=10)
    messages = [
        {"role": "system", "content": "You are a helpful AI assistant in a group chat. Provide concise and friendly responses."}
    ]
    messages.extend(context)
    messages.append({"role": "user", "content": query})

    # Generate AI message ID (will be replaced by database ID)
    ai_message_id = f"ai_{timestamp.timestamp()}"

    # Notify clients in current room that AI is starting response
    await sio.emit('ai_response_start', {
        'id': ai_message_id,
        'username': 'AI Assistant',
        'triggered_by': username,
        'timestamp': timestamp.isoformat()
    }, room=f"room_{room_id}")

    # Stream AI response
    full_response = ""

    try:
        # Run synchronous generator in thread pool
        loop = asyncio.get_event_loop()

        def sync_stream():
            """Wrapper to run sync generator"""
            chunks = []
            try:
                for chunk in chat_completion_stream(
                    messages=messages,
                    model="deepseek-chat",
                    temperature=0.7
                ):
                    chunks.append(chunk)
            except Exception as e:
                print(f"[DeepSeek Error] {e}")
                raise
            return chunks

        # Get all chunks from sync generator
        chunks = await loop.run_in_executor(executor, sync_stream)

        # Stream chunks to clients in current room only
        for chunk in chunks:
            full_response += chunk
            await sio.emit('ai_response_chunk', {
                'id': ai_message_id,
                'chunk': chunk
            }, room=f"room_{room_id}")
            # Small delay for better streaming effect
            await asyncio.sleep(0.01)

        # Notify completion to current room only
        await sio.emit('ai_response_end', {
            'id': ai_message_id
        }, room=f"room_{room_id}")

        # Save AI response to database
        with get_db() as db:
            db_message = DatabaseHelper.add_message(
                db,
                room_id=room_id,
                user_id=None,  # AI has no user_id
                content=full_response,
                is_ai=True,
                triggered_by=user_db_id
            )
            print(f"[AI] Completed response ({len(full_response)} chars) [Room: {room_id}, DB ID: {db_message.id}]")

    except Exception as e:
        print(f"[AI Stream Error] {e}")
        await sio.emit('ai_error', {
            'message': f'AI response failed: {str(e)}'
        })


# ========== Socket.IO Events ==========
@sio.event
async def connect(sid, environ, auth):
    """Client connected - supports optional token authentication"""
    token = auth.get('token') if auth else None

    if token:
        # Token-based authentication - just verify, don't add user yet
        # User will be added in user_join event
        with get_db() as db:
            user = get_user_by_token(db, token)
            if user:
                print(f"[Socket.IO] Valid token for user {user.username} (sid: {sid})")
                return True
            else:
                print(f"[Socket.IO] Invalid token for sid: {sid}")
                # Don't reject - allow fallback to username login

    print(f"[Socket.IO] Client connected: {sid} (no token)")


@sio.event
async def disconnect(sid):
    """Client disconnected"""
    username = chat_state.remove_user(sid)
    if username:
        print(f"[Socket.IO] User {username} disconnected")
        await sio.emit('user_left', {
            'username': username,
            'user_count': len(chat_state.users),
            'timestamp': datetime.now().isoformat()
        })


@sio.event
async def user_join(sid, data):
    """User joins the chat room"""
    username = data.get('username', '').strip()

    if not username:
        await sio.emit('error', {'message': 'Username is required'}, room=sid)
        return

    # Check if username already taken by OTHER online users (not current sid)
    existing_user = next((u for s, u in chat_state.users.items() if s != sid and u.username == username), None)
    if existing_user:
        await sio.emit('error', {'message': 'Username already taken'}, room=sid)
        return

    # Get or create user in database
    with get_db() as db:
        db_user = DatabaseHelper.get_or_create_user(db, username)
        user_db_id = db_user.id

        # Add user to state (or update if reconnecting)
        chat_state.add_user(sid, username, user_db_id)

        # Set user to default room initially
        chat_state.set_user_room(sid, chat_state.default_room_id)

        print(f"[Socket.IO] User {username} joined (sid: {sid}, db_id: {user_db_id})")

        # Add user to default room
        DatabaseHelper.add_user_to_room(db, user_db_id, chat_state.default_room_id)

        # Get user's room list
        user_rooms = RoomManager.list_user_rooms(db, user_db_id)
        rooms_data = [room.to_dict() for room in user_rooms]

    # Join default room's Socket.IO room for message broadcasting
    await sio.enter_room(sid, f"room_{chat_state.default_room_id}")

    # Broadcast to all clients
    await sio.emit('user_joined', {
        'username': username,
        'user_count': len(chat_state.users),
        'timestamp': datetime.now().isoformat()
    })

    # Send user's room list
    await sio.emit('room_list', {'rooms': rooms_data}, room=sid)

    # Send chat history from default room
    with get_db() as db:
        messages = DatabaseHelper.get_recent_messages(db, chat_state.default_room_id, limit=50)
        history = [msg.to_dict() for msg in messages]
        await sio.emit('chat_history', {'messages': history, 'room_id': chat_state.default_room_id}, room=sid)


@sio.event
async def chat_message(sid, data):
    """Handle incoming chat message"""
    username = chat_state.get_username(sid)
    if not username:
        await sio.emit('error', {'message': 'Not authenticated'}, room=sid)
        return

    content = data.get('message', '').strip()
    if not content:
        return

    timestamp = datetime.now()
    user_db_id = chat_state.get_user_db_id(sid)
    current_room_id = chat_state.get_user_room(sid) or chat_state.default_room_id

    # Save to database
    with get_db() as db:
        db_message = DatabaseHelper.add_message(
            db,
            room_id=current_room_id,
            user_id=user_db_id,
            content=content,
            is_ai=False
        )
        message_dict = db_message.to_dict()

    # Broadcast to all clients in the same room only
    await sio.emit('chat_message', message_dict, room=f"room_{current_room_id}")

    print(f"[Chat] {username} in room {current_room_id}: {content[:50]}... [DB ID: {message_dict['id']}]")

    # Check if @AI is mentioned
    if detect_ai_mention(content):
        query = extract_ai_query(content)
        print(f"[AI] Triggered by {username} in room {current_room_id}, query: {query[:50]}...")

        # Add to AI processing queue
        await chat_state.ai_queue.put({
            'query': query,
            'username': username,
            'user_db_id': user_db_id,
            'room_id': current_room_id,
            'timestamp': timestamp
        })


# ========== Room Management Events ==========
@sio.event
async def create_room(sid, data):
    """Create a new chat room"""
    username = chat_state.get_username(sid)
    user_db_id = chat_state.get_user_db_id(sid)

    if not username or not user_db_id:
        await sio.emit('error', {'message': 'Not authenticated'}, room=sid)
        return

    room_name = data.get('name', '').strip()
    room_description = data.get('description', '').strip()
    is_private = data.get('is_private', False)

    if not room_name:
        await sio.emit('error', {'message': 'Room name is required'}, room=sid)
        return

    with get_db() as db:
        try:
            room = RoomManager.create_room(db, room_name, room_description, user_db_id, is_private)
            print(f"[Room] {username} created room: {room_name} (id: {room.id})")

            # Send success to creator
            await sio.emit('room_created', {
                'room': room.to_dict(),
                'message': f"Room '{room_name}' created successfully"
            }, room=sid)

            # Broadcast to all users if public
            if not is_private:
                await sio.emit('room_list_updated', {
                    'action': 'created',
                    'room': room.to_dict()
                })

        except ValueError as e:
            await sio.emit('error', {'message': str(e)}, room=sid)


@sio.event
async def join_room(sid, data):
    """Join a chat room"""
    username = chat_state.get_username(sid)
    user_db_id = chat_state.get_user_db_id(sid)

    if not username or not user_db_id:
        await sio.emit('error', {'message': 'Not authenticated'}, room=sid)
        return

    room_id = data.get('room_id')
    if not room_id:
        await sio.emit('error', {'message': 'Room ID is required'}, room=sid)
        return

    with get_db() as db:
        try:
            # Check if room exists
            room = RoomManager.get_room_by_id(db, room_id)
            if not room:
                await sio.emit('error', {'message': 'Room not found'}, room=sid)
                return

            # Join room in database
            RoomManager.join_room(db, user_db_id, room_id)

            # Join Socket.IO room
            await sio.enter_room(sid, f"room_{room_id}")

            # Set as current room
            chat_state.set_user_room(sid, room_id)

            print(f"[Room] {username} joined room: {room.name} (id: {room_id})")

            # Load room history
            messages = DatabaseHelper.get_recent_messages(db, room_id, limit=50)
            history = [msg.to_dict() for msg in messages]

            await sio.emit('room_joined', {
                'room': room.to_dict(include_members=True),
                'messages': history
            }, room=sid)

            # Notify room members
            await sio.emit('user_joined_room', {
                'username': username,
                'room_id': room_id,
                'timestamp': datetime.now().isoformat()
            }, room=f"room_{room_id}", skip_sid=sid)

        except ValueError as e:
            await sio.emit('error', {'message': str(e)}, room=sid)


@sio.event
async def leave_room(sid, data):
    """Leave a chat room"""
    username = chat_state.get_username(sid)
    user_db_id = chat_state.get_user_db_id(sid)

    if not username or not user_db_id:
        return

    room_id = data.get('room_id')
    if not room_id:
        return

    with get_db() as db:
        # Don't allow leaving default room
        default_room = DatabaseHelper.get_default_room(db)
        if room_id == default_room.id:
            await sio.emit('error', {'message': 'Cannot leave default room'}, room=sid)
            return

        RoomManager.leave_room(db, user_db_id, room_id)

    # Leave Socket.IO room
    await sio.leave_room(sid, f"room_{room_id}")

    print(f"[Room] {username} left room: {room_id}")

    # Notify remaining members
    await sio.emit('user_left_room', {
        'username': username,
        'room_id': room_id,
        'timestamp': datetime.now().isoformat()
    }, room=f"room_{room_id}")

    await sio.emit('room_left', {'room_id': room_id}, room=sid)


@sio.event
async def switch_room(sid, data):
    """Switch to a different room"""
    username = chat_state.get_username(sid)
    user_db_id = chat_state.get_user_db_id(sid)

    if not username or not user_db_id:
        await sio.emit('error', {'message': 'Not authenticated'}, room=sid)
        return

    room_id = data.get('room_id')
    if not room_id:
        await sio.emit('error', {'message': 'Room ID is required'}, room=sid)
        return

    with get_db() as db:
        # Check if user is member of room
        if not RoomManager.is_user_in_room(db, user_db_id, room_id):
            await sio.emit('error', {'message': 'You are not a member of this room'}, room=sid)
            return

        # Leave previous Socket.IO room if exists
        old_room_id = chat_state.get_user_room(sid)
        if old_room_id:
            await sio.leave_room(sid, f"room_{old_room_id}")

        # Join new Socket.IO room
        await sio.enter_room(sid, f"room_{room_id}")

        # Set as current room
        chat_state.set_user_room(sid, room_id)

        # Load room history
        messages = DatabaseHelper.get_recent_messages(db, room_id, limit=50)
        history = [msg.to_dict() for msg in messages]

        room = RoomManager.get_room_by_id(db, room_id)

        await sio.emit('room_switched', {
            'room': room.to_dict(include_members=True),
            'messages': history
        }, room=sid)

        print(f"[Room] {username} switched to room: {room.name} (id: {room_id})")


@sio.event
async def list_rooms(sid, data):
    """Get list of available rooms"""
    user_db_id = chat_state.get_user_db_id(sid)

    if not user_db_id:
        await sio.emit('error', {'message': 'Not authenticated'}, room=sid)
        return

    with get_db() as db:
        # Get user's rooms
        user_rooms = RoomManager.list_user_rooms(db, user_db_id)
        # Get public rooms
        public_rooms = RoomManager.list_public_rooms(db)

        # Combine and deduplicate
        all_rooms = {room.id: room for room in user_rooms + public_rooms}
        rooms_data = [room.to_dict() for room in all_rooms.values()]

        await sio.emit('room_list', {'rooms': rooms_data}, room=sid)


@sio.event
async def delete_room(sid, data):
    """Delete a chat room (creator only)"""
    username = chat_state.get_username(sid)
    user_db_id = chat_state.get_user_db_id(sid)

    if not username or not user_db_id:
        await sio.emit('error', {'message': 'Not authenticated'}, room=sid)
        return

    room_id = data.get('room_id')
    if not room_id:
        await sio.emit('error', {'message': 'Room ID is required'}, room=sid)
        return

    with get_db() as db:
        try:
            RoomManager.delete_room(db, room_id, user_db_id)
            print(f"[Room] {username} deleted room: {room_id}")

            # Notify all users
            await sio.emit('room_deleted', {
                'room_id': room_id,
                'message': f"Room was deleted by {username}"
            })

        except ValueError as e:
            await sio.emit('error', {'message': str(e)}, room=sid)


# ========== Pydantic Models for API ==========
class RegisterRequest(BaseModel):
    username: str
    password: str
    email: Optional[str] = None


class LoginRequest(BaseModel):
    username: str
    password: str


# ========== HTTP Endpoints ==========
@app.get("/")
def read_root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "AI Group Chat",
        "users_online": len(chat_state.users),
        "ai_processing": chat_state.ai_processing
    }


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "users_online": len(chat_state.users),
        "ai_processing": chat_state.ai_processing
    }


# ========== Authentication Endpoints ==========
@app.post("/api/auth/register")
async def register(req: RegisterRequest):
    """Register a new user"""
    with get_db() as db:
        try:
            user = create_user(db, req.username, req.password, req.email)
            token = create_access_token({"sub": user.username, "user_id": user.id})
            return {
                "token": token,
                "user": user.to_dict()
            }
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            print(f"[Auth Error] Register: {e}")
            raise HTTPException(status_code=500, detail="Registration failed")


@app.post("/api/auth/login")
async def login(req: LoginRequest):
    """Login user"""
    with get_db() as db:
        user = authenticate_user(db, req.username, req.password)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid username or password")

        token = create_access_token({"sub": user.username, "user_id": user.id})
        return {
            "token": token,
            "user": user.to_dict()
        }


@app.get("/api/auth/me")
async def get_current_user(authorization: str = Header(None)):
    """Get current authenticated user"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")

    token = authorization.replace("Bearer ", "")

    with get_db() as db:
        user = get_user_by_token(db, token)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid token")

        return user.to_dict()


# ========== Startup Event ==========
@app.on_event("startup")
async def startup_event():
    """Start background tasks on startup"""
    print("[Server] Starting AI Group Chat Backend...")
    print(f"[Server] DEEPSEEK_API_KEY: {'Set' if os.getenv('DEEPSEEK_API_KEY') else 'NOT SET!'}")

    # Initialize database
    init_db()
    print("[Database] Database initialized")

    # Get default room ID
    with get_db() as db:
        default_room = DatabaseHelper.get_default_room(db)
        if default_room:
            chat_state.default_room_id = default_room.id
            print(f"[Database] Default room ID: {chat_state.default_room_id}")

    # Start AI queue processor
    asyncio.create_task(process_ai_queue())
    print("[Server] AI queue processor started")


# ========== ASGI Application ==========
# Wrap FastAPI with Socket.IO
asgi_app = socketio.ASGIApp(
    sio,
    other_asgi_app=app,
    socketio_path='socket.io'
)


if __name__ == "__main__":
    import uvicorn
    print("Run with: uvicorn main:asgi_app --reload")
    uvicorn.run(asgi_app, host="0.0.0.0", port=8000)
