import { useState, useEffect, useRef } from 'react';
import { useSocket } from './hooks/useSocket';

function App() {
  const { socket, connected } = useSocket();

  // Login state
  const [username, setUsername] = useState('');
  const [isJoined, setIsJoined] = useState(false);

  // Chat state
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [userCount, setUserCount] = useState(0);
  const [aiStreaming, setAiStreaming] = useState(false);

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
    };
  }, [socket]);

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

  // Login screen
  if (!isJoined) {
    return (
      <div className="login-screen">
        <div className="login-box">
          <h1>🤖 AI Group Chat</h1>
          <p>Enter your username to start chatting</p>
          <input
            type="text"
            className="login-input"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Enter username"
            maxLength={20}
            disabled={!connected}
            autoFocus
          />
          <button
            className="login-button"
            onClick={handleJoin}
            disabled={!connected || !username.trim()}
          >
            {connected ? 'Join Chat' : 'Connecting...'}
          </button>
          <p className="login-hint">
            💡 Use <code>@AI</code> in messages to talk with the AI assistant
          </p>
        </div>
      </div>
    );
  }

  // Chat screen
  return (
    <div className="chat-screen">
      {/* Header */}
      <div className="chat-header">
        <h2>🤖 AI Group Chat</h2>
        <div className="user-info">
          <span className="current-user">👤 {username}</span>
          <span className="user-count">
            {userCount} user{userCount !== 1 ? 's' : ''} online
          </span>
          {!connected && (
            <span className="disconnected-badge">⚠️ Disconnected</span>
          )}
        </div>
      </div>

      {/* Messages */}
      <div className="messages-container">
        {messages.length === 0 ? (
          <div className="empty-state">
            <p>👋 Welcome to the AI Group Chat!</p>
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
  );
}

export default App;
