# AI Group Chat 功能扩展计划

## 需求分析

**用户需求：**
- 关注方向：数据持久化 + 用户系统 + 聊天增强 + AI 能力
- 使用场景：团队协作
- 开发周期：短期 (1-2周)

**当前系统状态：**
- ✅ 基础群聊（实时消息同步）
- ✅ @AI 触发（DeepSeek 流式响应）
- ✅ 消息历史（内存存储 500 条）
- ✅ 跨设备访问
- ❌ 无数据持久化（重启丢失）
- ❌ 无用户认证（仅用户名）
- ❌ 单一聊天室
- ❌ 无文件分享

---

## 功能扩展路线图

### 🎯 Phase 1: 核心基础设施 (2-3 天)
**目标：建立数据持久化和用户系统基础**

#### 1.1 SQLite 数据库集成
**优先级：P0 - 必需**

**功能：**
- 持久化聊天消息
- 保存用户信息
- 聊天室配置

**数据库设计：**
```sql
-- 用户表
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255),  -- 后续添加
    email VARCHAR(100),
    avatar_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP
);

-- 聊天室表
CREATE TABLE rooms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_private BOOLEAN DEFAULT 0
);

-- 消息表
CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_id INTEGER REFERENCES rooms(id),
    user_id INTEGER,  -- NULL for AI
    content TEXT NOT NULL,
    is_ai BOOLEAN DEFAULT 0,
    triggered_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 房间成员表
CREATE TABLE room_members (
    room_id INTEGER REFERENCES rooms(id),
    user_id INTEGER REFERENCES users(id),
    role VARCHAR(20) DEFAULT 'member',  -- admin, member
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (room_id, user_id)
);
```

**实现步骤：**
1. 创建 `backend/database.py` - SQLite 连接和 ORM
2. 创建 `backend/models.py` - 数据模型
3. 创建 `backend/migrations/` - 数据库迁移脚本
4. 修改 `backend/main.py` - 集成数据库操作
5. 添加启动时自动创建数据库

**关键代码文件：**
- `backend/database.py` (新建，~150 行)
- `backend/models.py` (新建，~100 行)
- `backend/main.py` (修改，添加数据库操作)

---

#### 1.2 简易用户认证系统
**优先级：P0 - 必需**

**功能：**
- 用户注册（用户名 + 密码）
- 用户登录（JWT Token）
- 会话管理
- 用户资料查看

**技术方案：**
- 使用 `passlib` 加密密码
- 使用 `python-jose` 生成 JWT
- Socket.IO 认证中间件

**API 端点：**
```
POST /api/auth/register  - 注册
POST /api/auth/login     - 登录
GET  /api/auth/me        - 获取当前用户
POST /api/auth/logout    - 登出
```

**Socket.IO 认证流程：**
```python
@sio.event
async def connect(sid, environ, auth):
    token = auth.get('token')
    user = verify_jwt_token(token)
    if not user:
        raise ConnectionRefusedError('Unauthorized')
    # 保存用户会话
```

**实现步骤：**
1. 创建 `backend/auth.py` - JWT 和密码处理
2. 添加 HTTP 认证端点到 `backend/main.py`
3. 修改 Socket.IO 连接认证
4. 前端添加登录/注册界面
5. 前端保存 Token 到 localStorage

**关键代码文件：**
- `backend/auth.py` (新建，~120 行)
- `backend/main.py` (修改，添加 HTTP 端点)
- `frontend/src/components/AuthScreen.jsx` (新建，~150 行)
- `frontend/src/hooks/useAuth.js` (新建，~80 行)

---

### 🚀 Phase 2: 聊天功能增强 (3-4 天)
**目标：提升团队协作体验**

#### 2.1 多聊天室功能
**优先级：P0 - 必需（团队协作核心需求）**

**功能：**
- 创建/删除聊天室
- 加入/离开聊天室
- 聊天室列表
- 切换聊天室
- 聊天室权限（公开/私有）

**UI 改动：**
```
左侧边栏：
  - 聊天室列表
  - 创建聊天室按钮
  - 搜索聊天室

主区域：
  - 当前聊天室名称
  - 聊天室成员列表
  - 聊天室设置
```

**Socket.IO 事件扩展：**
```
create_room       - 创建聊天室
join_room         - 加入聊天室
leave_room        - 离开聊天室
list_rooms        - 获取聊天室列表
room_created      - 聊天室创建通知
room_updated      - 聊天室更新通知
```

**实现步骤：**
1. 修改后端支持多房间管理
2. 添加房间相关 Socket.IO 事件
3. 前端重构 UI 结构（侧边栏 + 主区域）
4. 实现房间切换和状态管理
5. 添加房间创建/管理界面

**关键代码文件：**
- `backend/room_manager.py` (新建，~200 行)
- `backend/main.py` (修改，添加房间事件)
- `frontend/src/components/RoomList.jsx` (新建，~120 行)
- `frontend/src/components/CreateRoom.jsx` (新建，~80 行)
- `frontend/src/App.jsx` (重构，支持多房间)

---

#### 2.2 增强聊天功能
**优先级：P1 - 重要**

**功能清单：**

**A. @用户名 提及**
- 输入 @ 时显示用户列表
- 被 @ 的用户收到通知
- 消息中高亮显示 @

**B. 消息操作**
- 编辑消息（5分钟内）
- 删除消息（自己的消息）
- 回复消息（引用）
- 消息反应（emoji）

**C. 富文本支持**
- Markdown 渲染
- 代码高亮
- 链接预览
- Emoji 选择器

**D. 消息搜索**
- 关键词搜索历史消息
- 按用户筛选
- 按日期范围筛选

**实现优先级：**
1. @用户名提及（2天）
2. 消息操作：编辑/删除（1天）
3. Markdown 渲染（半天）
4. 消息搜索（1天）

**关键代码文件：**
- `backend/message_handler.py` (新建，~150 行)
- `frontend/src/components/MessageItem.jsx` (重构，~200 行)
- `frontend/src/components/MentionInput.jsx` (新建，~100 行)
- `frontend/src/components/SearchBar.jsx` (新建，~80 行)

---

#### 2.3 文件分享
**优先级：P1 - 重要（团队协作常用）**

**功能：**
- 图片上传和预览
- 文件上传（限制 10MB）
- 文件下载
- 缩略图生成

**技术方案：**
- 本地文件存储（`backend/uploads/`）
- 或使用对象存储（阿里云 OSS / AWS S3）

**安全措施：**
- 文件类型白名单
- 大小限制
- 病毒扫描（可选）

**实现步骤：**
1. 添加文件上传 HTTP 端点
2. 实现文件存储和访问
3. 前端文件选择和上传 UI
4. 消息中显示文件/图片
5. 图片预览和下载功能

**关键代码文件：**
- `backend/file_handler.py` (新建，~150 行)
- `backend/main.py` (添加文件上传端点)
- `frontend/src/components/FileUpload.jsx` (新建，~100 行)
- `frontend/src/components/ImagePreview.jsx` (新建，~80 行)

---

### 🤖 Phase 3: AI 能力提升 (2-3 天)
**目标：增强 AI 助手能力**

#### 3.1 多 AI 模型支持
**优先级：P1 - 重要**

**功能：**
- 支持多个 AI 模型（DeepSeek, GPT, Claude 等）
- 用户可选择模型
- 模型参数配置（temperature, max_tokens）
- 模型切换无缝集成

**UI 设计：**
```
设置面板：
  - AI 模型选择下拉框
  - Temperature 滑块 (0-1)
  - Max Tokens 输入框
  - 保存配置按钮
```

**后端架构：**
```python
# backend/ai/
#   ├── base.py          - AI 基类
#   ├── deepseek.py      - DeepSeek 实现
#   ├── openai.py        - OpenAI 实现
#   ├── claude.py        - Claude 实现
#   └── factory.py       - AI 工厂模式
```

**实现步骤：**
1. 重构 AI 客户端为抽象基类
2. 实现多个 AI provider
3. 添加模型选择接口
4. 前端添加 AI 设置界面
5. 支持按房间配置默认模型

**关键代码文件：**
- `backend/ai/base.py` (新建，~100 行)
- `backend/ai/deepseek.py` (重构现有代码)
- `backend/ai/factory.py` (新建，~80 行)
- `frontend/src/components/AISettings.jsx` (新建，~120 行)

---

#### 3.2 AI 上下文管理
**优先级：P2 - 可选**

**功能：**
- 扩展上下文窗口（支持更长对话历史）
- 智能摘要（自动总结长对话）
- 重要信息标记
- 上下文压缩

**技术方案：**
- 使用向量数据库（Chroma / Faiss）
- 存储消息 embeddings
- RAG（检索增强生成）

**实现步骤：**
1. 集成向量数据库
2. 实现消息 embedding 生成
3. 相似度检索相关历史
4. AI 调用时附加检索结果
5. 添加对话摘要功能

**关键代码文件：**
- `backend/ai/memory.py` (新建，~150 行)
- `backend/ai/embeddings.py` (新建，~100 行)
- `backend/main.py` (集成上下文检索)

---

#### 3.3 AI 高级功能
**优先级：P2 - 可选（时间允许）**

**功能清单：**

**A. AI 指令模板**
- 预设常用指令（如"总结对话"、"翻译"、"代码审查"）
- 快捷键触发
- 自定义指令

**B. AI 多模态**
- 图片识别（上传图片给 AI 分析）
- 语音转文字
- 文字转语音

**C. AI 工具调用**
- 搜索功能（联网搜索）
- 代码执行（安全沙箱）
- API 集成（天气、日历等）

**实现优先级：**
1. AI 指令模板（1天）
2. 图片识别（1天，需要支持多模态的模型）
3. 工具调用（2天，需要安全机制）

---

### 🎨 Phase 4: 用户体验优化 (1-2 天)
**目标：提升易用性和美观度**

#### 4.1 UI/UX 优化

**功能清单：**
- 主题切换（浅色/深色）
- 自定义配色
- 头像上传和显示
- 在线状态指示器
- 打字指示器（"XXX is typing..."）
- 消息已读状态
- 通知提示音
- 桌面通知（Notification API）

**实现步骤：**
1. 添加主题系统（CSS 变量）
2. 实现头像上传和存储
3. Socket.IO 添加 typing 事件
4. 消息已读状态跟踪
5. 浏览器通知集成

**关键代码文件：**
- `frontend/src/styles/themes.css` (新建)
- `frontend/src/hooks/useTheme.js` (新建，~60 行)
- `frontend/src/components/Avatar.jsx` (新建，~80 行)
- `frontend/src/utils/notifications.js` (新建，~50 行)

---

#### 4.2 性能优化

**优化项：**
- 消息虚拟滚动（处理大量消息）
- 图片懒加载
- WebSocket 连接优化
- 前端代码分割
- 缓存策略

**实现：**
- 使用 `react-window` 虚拟滚动
- 使用 `IntersectionObserver` 懒加载
- 添加 Service Worker
- Vite 打包优化

---

### 📊 Phase 5: 管理和监控 (可选扩展)
**目标：支持生产环境部署**

#### 5.1 管理后台

**功能：**
- 用户管理（查看、禁用）
- 聊天室管理
- 消息审核
- 数据统计

#### 5.2 系统监控

**功能：**
- 在线用户数监控
- 消息吞吐量统计
- AI 调用统计和成本
- 错误日志收集

#### 5.3 部署优化

**技术方案：**
- Docker 容器化
- Nginx 反向代理
- Redis 缓存和会话
- PostgreSQL 替换 SQLite

---

## 短期实施计划 (1-2周)

### 第一周：核心基础

**Day 1-2：数据持久化**
- [ ] SQLite 数据库设计和集成
- [ ] 消息持久化
- [ ] 用户信息存储
- [ ] 数据库迁移脚本

**Day 3-4：用户认证**
- [ ] JWT 认证系统
- [ ] 注册/登录 API
- [ ] Socket.IO 认证中间件
- [ ] 前端登录界面

**Day 5：多聊天室基础**
- [ ] 房间数据模型
- [ ] 创建/加入房间 API
- [ ] 房间列表功能

### 第二周：功能增强

**Day 6-7：多聊天室完善**
- [ ] 前端房间切换 UI
- [ ] 房间成员管理
- [ ] 房间权限控制

**Day 8-9：聊天功能增强**
- [ ] @用户名提及
- [ ] 消息编辑/删除
- [ ] Markdown 渲染

**Day 10-11：文件分享**
- [ ] 文件上传 API
- [ ] 图片预览
- [ ] 文件下载

**Day 12-14：AI 增强和优化**
- [ ] 多模型支持框架
- [ ] AI 设置界面
- [ ] UI/UX 优化
- [ ] 测试和 bug 修复

---

## 技术债务和风险

### 已知问题：

1. **并发性能**
   - 当前单进程架构
   - 建议：添加 Redis 支持多进程

2. **安全性**
   - 无 HTTPS（生产环境必需）
   - 无 SQL 注入防护（使用 ORM）
   - 无 XSS 防护（前端输入清理）

3. **可扩展性**
   - SQLite 不适合大规模
   - 建议：生产环境迁移 PostgreSQL

### 风险缓解：

- 优先实现 MVP 功能
- 持续测试和代码审查
- 文档完善
- 版本管理（Git 分支策略）

---

## 依赖库更新

### 后端新增：
```txt
# 数据库
sqlalchemy==2.0.23
alembic==1.13.0

# 认证
passlib==1.7.4
python-jose[cryptography]==3.3.0
python-multipart==0.0.6

# 可选
pillow==10.1.0  # 图片处理
redis==5.0.1    # 缓存
```

### 前端新增：
```json
{
  "dependencies": {
    "react-router-dom": "^6.20.0",
    "react-markdown": "^9.0.0",
    "react-window": "^1.8.10",
    "axios": "^1.6.0"
  }
}
```

---

## 预期成果

### 第一周结束：
✅ 数据持久化（重启不丢失）
✅ 用户登录/注册
✅ 多聊天室切换

### 第二周结束：
✅ @用户名提及
✅ 消息编辑/删除
✅ 文件/图片分享
✅ 多 AI 模型支持
✅ 优化的 UI/UX

### 技术指标：
- 支持 100+ 并发用户
- 消息延迟 < 50ms
- 数据库查询 < 100ms
- 前端首屏加载 < 2s

---

## 后续扩展方向

- 移动端适配（PWA）
- 国际化（i18n）
- 语音/视频通话
- 屏幕共享
- 集成第三方服务（Slack, Discord 等）
- 开放 API（Webhook）

---

## 总结

这个计划覆盖了你关注的所有方向，并针对**团队协作场景**优化。短期内（1-2周）可以实现：

**核心功能：**
1. 数据持久化 ✅
2. 用户认证系统 ✅
3. 多聊天室 ✅
4. @提及和消息操作 ✅
5. 文件分享 ✅
6. 多 AI 模型 ✅

这将把你的项目从 **MVP 演示** 提升到 **可用的团队协作工具**！
