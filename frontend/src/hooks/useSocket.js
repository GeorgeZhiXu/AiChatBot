import { useEffect, useState, useRef } from 'react';
import { io } from 'socket.io-client';

// Socket.IO URL configuration - adapts to development/production
const getSocketUrl = () => {
  // Production: use same host (nginx proxy handles /socket.io)
  if (import.meta.env.PROD) {
    return window.location.origin;
  }
  // Development: direct connection to backend
  if (window.location.hostname === 'localhost') {
    return 'http://localhost:8000';
  }
  return `http://${window.location.hostname}:8000`;
};

const SOCKET_URL = getSocketUrl();

/**
 * Socket.IO custom hook
 * Manages WebSocket connection with auto-reconnect
 * @param {string} token - Optional JWT token for authentication
 */
export function useSocket(token = null) {
  const [socket, setSocket] = useState(null);
  const [connected, setConnected] = useState(false);
  const socketRef = useRef(null);

  useEffect(() => {
    // Create Socket.IO connection with optional auth
    const connectionOptions = {
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      reconnectionAttempts: 5,
      timeout: 20000
    };

    // Add auth token if provided
    if (token) {
      connectionOptions.auth = { token };
    }

    const newSocket = io(SOCKET_URL, connectionOptions);

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
  }, []);

  return { socket, connected };
}
