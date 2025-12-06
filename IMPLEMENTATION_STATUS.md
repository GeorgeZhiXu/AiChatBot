# Phase 1 实施状态报告

## ✅ 已完成部分

### 1. 数据库基础设施 (100%)

**已创建文件：**
- ✅ `backend/models.py` - 完整的 SQLAlchemy 数据模型
  - User 模型（用户表）
  - Room 模型（聊天室表）
  - Message 模型（消息表）
  - room_members 关联表（多对多关系）

- ✅ `backend/database.py` - 数据库连接和辅助函数
  - 数据库引擎初始化
  - Session 管理
  - DatabaseHelper 工具类
  - 自动创建默认 "General" 聊天室

- ✅ `backend/auth.py` - 完整的 JWT 认证系统
  - 密码哈希（bcrypt）
  - JWT token 生成和验证
  - 用户认证函数
  - 用户创建和管理

- ✅ `backend/requirements.txt` - 更新依赖清单

**数据库表结构：**
```sql
-- users: 用户信息
-- rooms: 聊天室
-- messages: 消息记录
-- room_members: 用户-房间关系（多对多）
```

---

## 🚧 待完成部分

### 2. 后端集成 (需要2-3小时)

**需要修改 `backend/main.py`：**

#### A. 数据库初始化
```python
from database import init_db, get_db, DatabaseHelper
from models import User, Room, Message
from auth import create_access_token, verify_token, authenticate_user, create_user

# 在 startup_event 中添加
@app.on_event("startup")
async def startup_event():
    init_db()  # 初始化数据库
    # ...
```

#### B. HTTP 认证端点
添加以下 API 端点：

```python
@app.post("/api/auth/register")
async def register(username: str, password: str, email: str = None):
    with get_db() as db:
        try:
            user = create_user(db, username, password, email)
            token = create_access_token({"sub": username, "user_id": user.id})
            return {"token": token, "user": user.to_dict()}
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/auth/login")
async def login(username: str, password: str):
    with get_db() as db:
        user = authenticate_user(db, username, password)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        token = create_access_token({"sub": username, "user_id": user.id})
        return {"token": token, "user": user.to_dict()}

@app.get("/api/auth/me")
async def get_current_user(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401)
    token = authorization.replace("Bearer ", "")
    with get_db() as db:
        user = get_user_by_token(db, token)
        if not user:
            raise HTTPException(status_code=401)
        return user.to_dict()
```

#### C. Socket.IO 认证中间件
```python
@sio.event
async def connect(sid, environ, auth):
    token = auth.get('token') if auth else None

    if not token:
        # 兼容旧版本：允许无 token 连接（开发阶段）
        print(f"[Socket.IO] Client {sid} connected without authentication")
        return True

    with get_db() as db:
        user = get_user_by_token(db, token)
        if not user:
            raise ConnectionRefusedError('Invalid token')

        # 保存用户会话
        chat_state.users[sid] = user
        update_user_last_seen(db, user.id)
        print(f"[Socket.IO] User {user.username} authenticated")
```

#### D. 消息持久化
修改 `chat_message` 事件：

```python
@sio.event
async def chat_message(sid, data):
    # ... 现有逻辑 ...

    # 保存到数据库
    with get_db() as db:
        user = chat_state.users.get(sid)
        if user:
            room = DatabaseHelper.get_default_room(db)
            DatabaseHelper.add_message(
                db,
                room_id=room.id,
                user_id=user.id,
                content=content,
                is_ai=False
            )
```

#### E. 加载历史消息
修改 `user_join` 事件：

```python
@sio.event
async def user_join(sid, data):
    # ... 现有逻辑 ...

    # 从数据库加载历史消息
    with get_db() as db:
        room = DatabaseHelper.get_default_room(db)
        messages = DatabaseHelper.get_recent_messages(db, room.id, limit=50)
        history = [msg.to_dict() for msg in messages]
        await sio.emit('chat_history', {'messages': history}, room=sid)
```

---

### 3. 前端集成 (需要2-3小时)

**需要创建的文件：**

#### A. `frontend/src/hooks/useAuth.js`
```javascript
import { useState, useEffect } from 'react';
import axios from 'axios';

const API_URL = 'http://localhost:8000/api';

export function useAuth() {
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (token) {
      // 验证 token 并获取用户信息
      axios.get(`${API_URL}/auth/me`, {
        headers: { Authorization: `Bearer ${token}` }
      }).then(res => {
        setUser(res.data);
      }).catch(() => {
        setToken(null);
        localStorage.removeItem('token');
      }).finally(() => {
        setLoading(false);
      });
    } else {
      setLoading(false);
    }
  }, [token]);

  const login = async (username, password) => {
    const res = await axios.post(`${API_URL}/auth/login`, { username, password });
    setToken(res.data.token);
    setUser(res.data.user);
    localStorage.setItem('token', res.data.token);
  };

  const register = async (username, password, email) => {
    const res = await axios.post(`${API_URL}/auth/register`, { username, password, email });
    setToken(res.data.token);
    setUser(res.data.user);
    localStorage.setItem('token', res.data.token);
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('token');
  };

  return { token, user, loading, login, register, logout };
}
```

#### B. `frontend/src/components/AuthScreen.jsx`
```javascript
import { useState } from 'react';

export function AuthScreen({ onLogin }) {
  const [isLogin, setIsLogin] = useState(true);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [email, setEmail] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    try {
      if (isLogin) {
        await onLogin(username, password);
      } else {
        await onRegister(username, password, email);
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Authentication failed');
    }
  };

  return (
    <div className="auth-screen">
      <div className="auth-box">
        <h1>{isLogin ? 'Login' : 'Register'}</h1>
        <form onSubmit={handleSubmit}>
          <input
            type="text"
            placeholder="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          {!isLogin && (
            <input
              type="email"
              placeholder="Email (optional)"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          )}
          {error && <div className="error">{error}</div>}
          <button type="submit">{isLogin ? 'Login' : 'Register'}</button>
        </form>
        <button onClick={() => setIsLogin(!isLogin)}>
          {isLogin ? 'Need an account?' : 'Already have an account?'}
        </button>
      </div>
    </div>
  );
}
```

#### C. 修改 `frontend/src/App.jsx`
在最外层添加认证检查：

```javascript
import { useAuth } from './hooks/useAuth';
import { AuthScreen } from './components/AuthScreen';

function App() {
  const { token, user, loading, login, logout } = useAuth();
  const { socket, connected } = useSocket(token); // 传递 token

  if (loading) {
    return <div>Loading...</div>;
  }

  if (!token) {
    return <AuthScreen onLogin={login} />;
  }

  // 原有的聊天界面...
}
```

#### D. 修改 `frontend/src/hooks/useSocket.js`
添加 token 参数：

```javascript
export function useSocket(token) {
  useEffect(() => {
    const newSocket = io(SOCKET_URL, {
      auth: { token },  // 传递 token
      // ...
    });
    // ...
  }, [token]);
}
```

---

## 📝 实施建议

### 立即可测试（无需前端修改）

当前已完成的后端代码可以立即使用：

1. **数据库自动创建**
   ```bash
   # 启动后端时自动创建数据库和表
   cd backend
   python -c "from database import init_db; init_db()"
   ```

2. **测试 HTTP API**
   ```bash
   # 注册用户
   curl -X POST http://localhost:8000/api/auth/register \
     -H "Content-Type: application/json" \
     -d '{"username": "test", "password": "123456"}'

   # 登录
   curl -X POST http://localhost:8000/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username": "test", "password": "123456"}'
   ```

### 渐进式集成策略

**方案 A：快速演示（1小时）**
- 只实现后端数据库持久化
- 前端保持现有用户名登录
- 后端兼容无 token 连接

**方案 B：完整实现（4-6小时）**
- 完整实现后端认证
- 前端添加登录/注册界面
- 完整的 token 认证流程

**方案 C：分阶段实施（推荐）**
- Day 1: 后端数据库集成 + 消息持久化
- Day 2: 后端认证 API
- Day 3: 前端认证界面
- Day 4: 测试和优化

---

## 🎯 下一步行动

选择一个实施方案，告诉我：

1. **"继续实施方案 A"** - 我会完成后端集成（1小时）
2. **"继续实施方案 B"** - 我会完成完整实现（4-6小时）
3. **"继续实施方案 C"** - 我们分阶段进行
4. **"暂停，先测试现有代码"** - 我会帮你测试数据库功能

---

## 📚 参考资料

- SQLAlchemy 文档：https://docs.sqlalchemy.org/
- FastAPI 认证：https://fastapi.tiangolo.com/tutorial/security/
- JWT 最佳实践：https://tools.ietf.org/html/rfc7519
