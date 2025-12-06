import { useState } from 'react';

/**
 * Authentication Screen - Login and Register
 */
export function AuthScreen({ onLogin, onRegister }) {
  const [isLogin, setIsLogin] = useState(true);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [email, setEmail] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      if (isLogin) {
        await onLogin(username, password);
      } else {
        await onRegister(username, password, email || null);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const toggleMode = () => {
    setIsLogin(!isLogin);
    setError('');
  };

  return (
    <div className="auth-screen">
      <div className="auth-box">
        <h1>🤖 AI Group Chat</h1>
        <h2>{isLogin ? 'Login' : 'Create Account'}</h2>

        <form onSubmit={handleSubmit} className="auth-form">
          <input
            type="text"
            className="auth-input"
            placeholder="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
            minLength={3}
            maxLength={20}
            autoFocus
          />

          <input
            type="password"
            className="auth-input"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={6}
          />

          {!isLogin && (
            <input
              type="email"
              className="auth-input"
              placeholder="Email (optional)"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          )}

          {error && (
            <div className="auth-error">
              ⚠️ {error}
            </div>
          )}

          <button
            type="submit"
            className="auth-button"
            disabled={loading}
          >
            {loading ? 'Processing...' : (isLogin ? 'Login' : 'Register')}
          </button>
        </form>

        <button
          type="button"
          className="auth-toggle"
          onClick={toggleMode}
          disabled={loading}
        >
          {isLogin
            ? "Don't have an account? Register"
            : 'Already have an account? Login'
          }
        </button>

        <p className="auth-hint">
          💡 {isLogin
            ? 'Login to access your chat history'
            : 'Create an account to get started'}
        </p>
      </div>
    </div>
  );
}
