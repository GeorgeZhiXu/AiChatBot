import { useState, useEffect } from 'react';
import axios from 'axios';

// API URL configuration - adapts to development/production
const getApiUrl = () => {
  // Production: use same host (nginx proxy handles /aichatbot-api)
  if (import.meta.env.PROD) {
    return `${window.location.origin}/aichatbot-api`;
  }
  // Development: direct connection to backend
  if (window.location.hostname === 'localhost') {
    return 'http://localhost:8000/api';
  }
  return `http://${window.location.hostname}:8000/api`;
};

const API_URL = getApiUrl();

/**
 * Authentication hook
 * Uses gateway authentication (nginx X-Auth-User headers)
 */
export function useAuth() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Check gateway auth on mount
  useEffect(() => {
    axios.get(`${API_URL}/auth/gateway`)
      .then(res => {
        setUser(res.data);
        setLoading(false);
      })
      .catch(() => {
        setUser(null);
        setLoading(false);
      });
  }, []);

  const logout = () => {
    setUser(null);
    setError(null);
    // Redirect to gateway root (which will show the dashboard)
    window.location.href = '/';
  };

  return { user, loading, error, logout };
}
