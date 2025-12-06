"""
AI Group Chat Backend
Real-time group chat with AI assistant (@AI trigger)
Built with FastAPI + Socket.IO + DeepSeek AI
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
    """Global chat state manager"""
    def __init__(self):
        self.users: Dict[str, User] = {}  # sid -> User
        self.message_history: List[ChatMessage] = []
        self.ai_queue: asyncio.Queue = asyncio.Queue()
        self.ai_processing: bool = False
        self.max_history = 500  # Keep last 500 messages

    def add_user(self, sid: str, username: str):
        """Add a user to the chat"""
        self.users[sid] = User(sid, username, datetime.now())

    def remove_user(self, sid: str) -> Optional[str]:
        """Remove a user and return their username"""
        user = self.users.pop(sid, None)
        return user.username if user else None

    def get_username(self, sid: str) -> Optional[str]:
        """Get username by socket ID"""
        user = self.users.get(sid)
        return user.username if user else None

    def username_exists(self, username: str) -> bool:
        """Check if username already taken"""
        return any(u.username == username for u in self.users.values())

    def add_message(self, msg: ChatMessage):
        """Add message to history"""
        self.message_history.append(msg)
        # Limit history size
        if len(self.message_history) > self.max_history:
            self.message_history = self.message_history[-self.max_history:]

    def get_recent_messages(self, limit: int = 50) -> List[dict]:
        """Get recent messages for new users"""
        recent = self.message_history[-limit:]
        return [msg.to_dict() for msg in recent]

    def get_context_for_ai(self, max_messages: int = 10) -> List[Dict[str, str]]:
        """Get recent chat context for AI"""
        recent = self.message_history[-max_messages:]
        messages = []
        for msg in recent:
            role = "assistant" if msg.is_ai else "user"
            content = msg.content if msg.is_ai else f"[{msg.username}]: {msg.content}"
            messages.append({"role": role, "content": content})
        return messages


# Global state instance
chat_state = ChatState()

# Thread pool for blocking AI calls
executor = ThreadPoolExecutor(max_workers=2)


# ========== @AI Detection ==========
def detect_ai_mention(message: str) -> bool:
    """Detect if message contains @AI mention"""
    patterns = [
        r'@AI\b',
        r'@ai\b',
        r'@\s*AI\b',
        r'@\s*ai\b'
    ]
    return any(re.search(pattern, message, re.IGNORECASE) for pattern in patterns)


def extract_ai_query(message: str) -> str:
    """Extract actual query from @AI message"""
    # Remove @AI mention
    cleaned = re.sub(r'@\s*AI\b', '', message, flags=re.IGNORECASE).strip()
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
    timestamp = request['timestamp']

    print(f"[AI] Processing request from {username}: {query[:50]}...")

    # Build message context
    context = chat_state.get_context_for_ai(max_messages=10)
    messages = [
        {"role": "system", "content": "You are a helpful AI assistant in a group chat. Provide concise and friendly responses."}
    ]
    messages.extend(context)
    messages.append({"role": "user", "content": query})

    # Generate AI message ID
    ai_message_id = f"ai_{timestamp.timestamp()}"

    # Notify clients that AI is starting response
    await sio.emit('ai_response_start', {
        'id': ai_message_id,
        'username': 'AI Assistant',
        'triggered_by': username,
        'timestamp': timestamp.isoformat()
    })

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

        # Stream chunks to clients
        for chunk in chunks:
            full_response += chunk
            await sio.emit('ai_response_chunk', {
                'id': ai_message_id,
                'chunk': chunk
            })
            # Small delay for better streaming effect
            await asyncio.sleep(0.01)

        # Notify completion
        await sio.emit('ai_response_end', {
            'id': ai_message_id
        })

        # Save AI response to history
        ai_msg = ChatMessage(
            id=ai_message_id,
            username='AI Assistant',
            content=full_response,
            timestamp=timestamp,
            is_ai=True
        )
        chat_state.add_message(ai_msg)

        print(f"[AI] Completed response ({len(full_response)} chars)")

    except Exception as e:
        print(f"[AI Stream Error] {e}")
        await sio.emit('ai_error', {
            'message': f'AI response failed: {str(e)}'
        })


# ========== Socket.IO Events ==========
@sio.event
async def connect(sid, environ):
    """Client connected"""
    print(f"[Socket.IO] Client connected: {sid}")


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

    # Check if username already taken
    if chat_state.username_exists(username):
        await sio.emit('error', {'message': 'Username already taken'}, room=sid)
        return

    # Add user
    chat_state.add_user(sid, username)
    print(f"[Socket.IO] User {username} joined (sid: {sid})")

    # Broadcast to all clients
    await sio.emit('user_joined', {
        'username': username,
        'user_count': len(chat_state.users),
        'timestamp': datetime.now().isoformat()
    })

    # Send chat history to new user
    history = chat_state.get_recent_messages(limit=50)
    await sio.emit('chat_history', {'messages': history}, room=sid)


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

    # Generate message ID and timestamp
    message_id = f"{sid}_{datetime.now().timestamp()}"
    timestamp = datetime.now()

    # Save to history
    msg = ChatMessage(
        id=message_id,
        username=username,
        content=content,
        timestamp=timestamp,
        is_ai=False
    )
    chat_state.add_message(msg)

    # Broadcast to all clients
    await sio.emit('chat_message', msg.to_dict())

    print(f"[Chat] {username}: {content[:50]}...")

    # Check if @AI is mentioned
    if detect_ai_mention(content):
        query = extract_ai_query(content)
        print(f"[AI] Triggered by {username}, query: {query[:50]}...")

        # Add to AI processing queue
        await chat_state.ai_queue.put({
            'query': query,
            'username': username,
            'timestamp': timestamp
        })


# ========== HTTP Endpoints (Optional) ==========
@app.get("/")
def read_root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "AI Group Chat",
        "users_online": len(chat_state.users),
        "ai_processing": chat_state.ai_processing,
        "message_count": len(chat_state.message_history)
    }


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "users_online": len(chat_state.users),
        "ai_processing": chat_state.ai_processing
    }


# ========== Startup Event ==========
@app.on_event("startup")
async def startup_event():
    """Start background tasks on startup"""
    print("[Server] Starting AI Group Chat Backend...")
    print(f"[Server] DEEPSEEK_API_KEY: {'Set' if os.getenv('DEEPSEEK_API_KEY') else 'NOT SET!'}")

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
