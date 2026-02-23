import { useEffect, useState, useRef } from 'react';
import { io } from 'socket.io-client';

// Socket.IO URL configuration - adapts to development/production
const getSocketUrl = () => {
  // Production: use same host with /aichatbot-api path (nginx proxy handles it)
  if (import.meta.env.PROD) {
    return {
      url: window.location.origin,
      path: '/aichatbot-api/socket.io/'
    };
  }
  // Development: direct connection to backend
  if (window.location.hostname === 'localhost') {
    return { url: 'http://localhost:8000', path: '/socket.io/' };
  }
  return { url: `http://${window.location.hostname}:8000`, path: '/socket.io/' };
};

const SOCKET_URL = getSocketUrl();

/**
 * Socket.IO custom hook
 * Manages WebSocket connection with auto-reconnect
 * @param {string} username - Gateway-authenticated username
 */
export function useSocket(username = null) {
  const [socket, setSocket] = useState(null);
  const [connected, setConnected] = useState(false);
  const socketRef = useRef(null);

  useEffect(() => {
    // Create Socket.IO connection with gateway username auth
    const connectionOptions = {
      path: SOCKET_URL.path,
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      reconnectionAttempts: 5,
      timeout: 20000
    };

    // Pass username in auth handshake for gateway authentication
    if (username) {
      connectionOptions.auth = { username };
    }

    const newSocket = io(SOCKET_URL.url, connectionOptions);

    socketRef.current = newSocket;
    setSocket(newSocket);

    // Connection events
    newSocket.on('connect', () => {
      console.log('[Socket.IO] Connected to server');
      setConnected(true);
    });

    newSocket.on('disconnect', () => {
      console.log('[Socket.IO] Disconnected from server');
      setConnected(false);
    });

    newSocket.on('connect_error', (error) => {
      console.error('[Socket.IO] Connection error:', error);
      setConnected(false);
    });

    newSocket.on('reconnect', (attemptNumber) => {
      console.log(`[Socket.IO] Reconnected after ${attemptNumber} attempts`);
      setConnected(true);
    });

    newSocket.on('reconnect_failed', () => {
      console.error('[Socket.IO] Reconnection failed');
      setConnected(false);
    });

    // Cleanup on unmount
    return () => {
      console.log('[Socket.IO] Closing connection');
      newSocket.close();
    };
  }, [username]);

  return { socket, connected };
}
