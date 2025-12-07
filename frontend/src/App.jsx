import { useState, useEffect, useRef } from 'react';
import { useSocket } from './hooks/useSocket';
import { useAuth } from './hooks/useAuth';
import { AuthScreen } from './components/AuthScreen';
import { RoomList } from './components/RoomList';

function App() {
  const { token, user, loading: authLoading, login, register, logout } = useAuth();
  const { socket, connected } = useSocket(token);

  // Login state
  const [username, setUsername] = useState('');
  const [isJoined, setIsJoined] = useState(false);

  // Chat state
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [userCount, setUserCount] = useState(0);
  const [aiStreaming, setAiStreaming] = useState(false);

  // Room state
  const [rooms, setRooms] = useState([]);
  const [currentRoom, setCurrentRoom] = useState(null);

  // Auto-scroll ref
  const messagesEndRef = useRef(null);

  // Auto-scroll to bottom when messages update
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Socket.IO event listeners
  useEffect(() => {
    if (!socket) return;

    // User joined
    socket.on('user_joined', (data) => {
      setUserCount(data.user_count);
      setMessages(prev => [...prev, {
        id: `system_${Date.now()}`,
        type: 'system',
        content: `${data.username} joined the chat`,
        timestamp: data.timestamp
      }]);
    });

    // User left
    socket.on('user_left', (data) => {
      setUserCount(data.user_count);
      setMessages(prev => [...prev, {
        id: `system_${Date.now()}`,
        type: 'system',
        content: `${data.username} left the chat`,
        timestamp: data.timestamp
      }]);
    });

    // Chat history (when joining)
    socket.on('chat_history', (data) => {
      const history = data.messages.map(msg => ({
        ...msg,
        type: msg.is_ai ? 'ai' : 'user'
      }));
      setMessages(history);
      // Set current room if provided
      if (data.room_id && !currentRoom) {
        const room = rooms.find(r => r.id === data.room_id);
        if (room) setCurrentRoom(room);
      }
    });

    // Room list
    socket.on('room_list', (data) => {
      setRooms(data.rooms);
      // Set default room as current if not set
      if (!currentRoom && data.rooms.length > 0) {
        const defaultRoom = data.rooms.find(r => r.name === 'General') || data.rooms[0];
        setCurrentRoom(defaultRoom);
      }
    });

    // Room created (by current user)
    socket.on('room_created', (data) => {
      // Check if room already exists
      setRooms(prev => {
        const exists = prev.some(r => r.id === data.room.id);
        if (exists) return prev;
        return [...prev, data.room];
      });
      alert(data.message);
      // Auto-switch to new room
      handleRoomSwitch(data.room);
    });

    // Room list updated (by other users)
    socket.on('room_list_updated', (data) => {
      if (data.action === 'created') {
        setRooms(prev => {
          // Avoid duplicates
          const exists = prev.some(r => r.id === data.room.id);
          if (exists) return prev;
          return [...prev, data.room];
        });
      }
    });

    // Room joined
    socket.on('room_joined', (data) => {
      setCurrentRoom(data.room);
      const history = data.messages.map(msg => ({
        ...msg,
        type: msg.is_ai ? 'ai' : 'user'
      }));
      setMessages(history);
    });

    // Room switched
    socket.on('room_switched', (data) => {
      setCurrentRoom(data.room);
      const history = data.messages.map(msg => ({
        ...msg,
        type: msg.is_ai ? 'ai' : 'user'
      }));
      setMessages(history);
    });

    // Room deleted
    socket.on('room_deleted', (data) => {
      setRooms(prev => prev.filter(r => r.id !== data.room_id));
      if (currentRoom?.id === data.room_id) {
        // Switch to default room
        const defaultRoom = rooms.find(r => r.name === 'General');
        if (defaultRoom) {
          handleRoomSwitch(defaultRoom);
        }
      }
      alert(data.message);
    });

    // New chat message
    socket.on('chat_message', (data) => {
      setMessages(prev => [...prev, {
        ...data,
        type: 'user'
      }]);
    });

    // AI response start
    socket.on('ai_response_start', (data) => {
      setAiStreaming(true);
      setMessages(prev => [...prev, {
        id: data.id,
        username: data.username,
        content: '',
        type: 'ai',
        streaming: true,
        triggered_by: data.triggered_by,
        timestamp: data.timestamp
      }]);
    });

    // AI response chunk (streaming)
    socket.on('ai_response_chunk', (data) => {
      setMessages(prev => prev.map(msg =>
        msg.id === data.id
          ? { ...msg, content: msg.content + data.chunk }
          : msg
      ));
    });

    // AI response end
    socket.on('ai_response_end', (data) => {
      setAiStreaming(false);
      setMessages(prev => prev.map(msg =>
        msg.id === data.id
          ? { ...msg, streaming: false }
          : msg
      ));
    });

    // AI busy
    socket.on('ai_busy', (data) => {
      setMessages(prev => [...prev, {
        id: `system_${Date.now()}`,
        type: 'system',
        content: data.message
      }]);
    });

    // Errors
    socket.on('error', (data) => {
      alert(data.message);
    });

    socket.on('ai_error', (data) => {
      setMessages(prev => [...prev, {
        id: `error_${Date.now()}`,
        type: 'error',
        content: data.message
      }]);
      setAiStreaming(false);
    });

    // Cleanup
    return () => {
      socket.off('user_joined');
      socket.off('user_left');
      socket.off('chat_history');
      socket.off('chat_message');
      socket.off('ai_response_start');
      socket.off('ai_response_chunk');
      socket.off('ai_response_end');
      socket.off('ai_busy');
      socket.off('error');
      socket.off('ai_error');
      socket.off('room_list');
      socket.off('room_created');
      socket.off('room_list_updated');
      socket.off('room_joined');
      socket.off('room_switched');
      socket.off('room_deleted');
    };
  }, [socket, rooms, currentRoom]);

  // Join chat
  const handleJoin = () => {
    if (!username.trim() || !socket) return;
    socket.emit('user_join', { username: username.trim() });
    setIsJoined(true);
  };

  // Send message
  const handleSend = () => {
    if (!input.trim() || !socket) return;
    socket.emit('chat_message', { message: input });
    setInput('');
  };

  // Handle Enter key
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (isJoined) {
        handleSend();
      } else {
        handleJoin();
      }
    }
  };

  // Room operations
  const handleRoomSwitch = (room) => {
    if (!socket || room.id === currentRoom?.id) return;
    socket.emit('switch_room', { room_id: room.id });
  };

  const handleCreateRoom = ({ name, description, is_private }) => {
    if (!socket) return;
    socket.emit('create_room', { name, description, is_private });
  };

  const handleDeleteRoom = (roomId) => {
    if (!socket) return;
    socket.emit('delete_room', { room_id: roomId });
  };

  // Render message based on type
  const renderMessage = (msg) => {
    // System message
    if (msg.type === 'system') {
      return (
        <div key={msg.id} className="system-message">
          {msg.content}
        </div>
      );
    }

    // Error message
    if (msg.type === 'error') {
      return (
        <div key={msg.id} className="error-message">
          ⚠️ {msg.content}
        </div>
      );
    }

    // User or AI message
    const isAI = msg.type === 'ai';
    const time = new Date(msg.timestamp).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit'
    });

    return (
      <div key={msg.id} className={`message ${isAI ? 'ai-message' : 'user-message'}`}>
        <div className="message-header">
          <span className={`message-username ${isAI ? 'ai-username' : ''}`}>
            {msg.username}
          </span>
          {msg.triggered_by && (
            <span className="triggered-info">
              (called by {msg.triggered_by})
            </span>
          )}
          <span className="message-time">{time}</span>
        </div>
        <div className="message-content">
          {msg.content}
          {msg.streaming && <span className="cursor">▋</span>}
        </div>
      </div>
    );
  };

  // Authentication loading
  if (authLoading) {
    return (
      <div className="loading-screen">
        <div className="loading-spinner">Loading...</div>
      </div>
    );
  }

  // Not authenticated - show login/register
  if (!token || !user) {
    return <AuthScreen onLogin={login} onRegister={register} />;
  }

  // Authenticated but not joined chat - auto-join
  if (!isJoined) {
    // Auto-set username from authenticated user and join
    if (user && connected && socket) {
      setUsername(user.username);
      setIsJoined(true);
      socket.emit('user_join', { username: user.username });
    }

    return (
      <div className="login-screen">
        <div className="login-box">
          <h1>🤖 AI Group Chat</h1>
          <p>Welcome, {user.username}!</p>
          <p>Connecting to chat...</p>
        </div>
      </div>
    );
  }

  // Chat screen
  return (
    <div className="chat-screen">
      {/* Room Sidebar */}
      <RoomList
        rooms={rooms}
        currentRoom={currentRoom}
        onRoomSwitch={handleRoomSwitch}
        onCreateRoom={handleCreateRoom}
        onDeleteRoom={handleDeleteRoom}
      />

      {/* Main Chat Area */}
      <div className="chat-main">
        {/* Header */}
        <div className="chat-header">
          <div className="header-left">
            <h2>{currentRoom?.name || 'AI Group Chat'}</h2>
            {currentRoom?.description && (
              <span className="room-description">{currentRoom.description}</span>
            )}
          </div>
          <div className="user-info">
            <span className="current-user">👤 {username}</span>
            <span className="user-count">
              {userCount} user{userCount !== 1 ? 's' : ''} online
            </span>
            {!connected && (
              <span className="disconnected-badge">⚠️ Disconnected</span>
            )}
            <button className="logout-btn-small" onClick={logout}>Logout</button>
          </div>
        </div>

        {/* Messages */}
        <div className="messages-container">
          {messages.length === 0 ? (
            <div className="empty-state">
              <p>👋 Welcome to {currentRoom?.name || 'the chat'}!</p>
              <p>Start a conversation or mention <code>@AI</code> for help</p>
            </div>
          ) : (
            messages.map(renderMessage)
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input bar */}
        <div className="input-bar">
          {aiStreaming && (
            <div className="ai-indicator">
              🤖 AI is responding...
            </div>
          )}
          <div className="input-wrapper">
            <input
              type="text"
              className="message-input"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Type a message... (use @AI to call AI assistant)"
              disabled={!connected}
            />
            <button
              className="send-button"
              onClick={handleSend}
              disabled={!connected || !input.trim()}
            >
              Send
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
