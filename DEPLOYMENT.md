# 🚀 AI Group Chat - Mac Mini 部署指南

本文档说明如何将 AI Group Chat 部署到 Mac mini 服务器，并配置 Gateway（nginx）访问。

## 📋 系统要求

- macOS 12.0+（Mac mini）
- Python 3.12+
- Node.js 16+
- Git
- Homebrew
- nginx

## 🎯 部署架构

```
Internet → Gateway (nginx :80) → Mac mini
                ├─→ Frontend (port 3030) - React App
                ├─→ Backend API (port 8030) - FastAPI
                └─→ Socket.IO (port 8030) - WebSocket
```

## 📦 端口配置

- **Frontend**: 3030（通过 npm serve）
- **Backend**: 8030（uvicorn）
- **Gateway**: 80（nginx 反向代理）

---

## 🛠️ 一次性手动配置（在 Mac mini 上执行）

### 1. 克隆代码到 Mac mini

```bash
cd ~
git clone https://github.com/GeorgeZhiXu/AiChatBot.git
cd AiChatBot
```

### 2. 运行自动安装脚本

```bash
cd ~/AiChatBot
./deployment/setup.sh
```

**脚本会自动完成：**
- ✅ 创建日志目录
- ✅ 配置 launchd 服务
- ✅ 安装 Python 依赖
- ✅ 安装 Node 依赖
- ✅ 构建前端生产版本
- ✅ 启动后端和前端服务
- ✅ 验证服务状态

**安装过程中会提示输入：**
- DeepSeek API Key
- JWT Secret Key（可自动生成）

### 3. 安装并配置 nginx

```bash
# 安装 nginx
brew install nginx

# 复制配置文件
sudo cp ~/AiChatBot/deployment/nginx-aichatbot.conf /usr/local/etc/nginx/servers/

# 编辑配置文件，替换 server_name
sudo nano /usr/local/etc/nginx/servers/nginx-aichatbot.conf
# 修改: server_name your-mac-mini.local;
# 改为: server_name 192.168.1.100;  # 你的 Mac mini IP

# 测试 nginx 配置
nginx -t

# 启动 nginx
brew services start nginx
```

### 4. 验证部署

```bash
# 本机测试
curl http://localhost:8030/health  # 后端健康检查
curl http://localhost:3030         # 前端页面

# Gateway 测试
curl http://your-mac-mini-ip/health  # 通过 nginx
open http://your-mac-mini-ip         # 浏览器访问
```

---

## 🔄 自动部署（GitHub Actions）

### 配置步骤

#### 1. 在 Mac mini 上生成 SSH 密钥（如果没有）

```bash
ssh-keygen -t ed25519 -C "github-actions"
cat ~/.ssh/id_ed25519.pub >> ~/.ssh/authorized_keys
cat ~/.ssh/id_ed25519  # 复制私钥
```

#### 2. 在 GitHub 仓库设置 Secrets

访问：https://github.com/GeorgeZhiXu/AiChatBot/settings/secrets/actions

添加以下 Secrets：
- `MAC_MINI_HOST`: Mac mini IP 地址（如 `192.168.1.100`）
- `MAC_MINI_USER`: Mac mini 用户名（如 `vivian`）
- `MAC_MINI_SSH_KEY`: SSH 私钥内容（从上面复制）
- `MAC_MINI_SSH_PORT`: SSH 端口（默认 `22`）

#### 3. 启用 SSH 远程登录

```bash
# 在 Mac mini 上
sudo systemsetup -setremotelogin on
```

#### 4. 推送代码触发自动部署

```bash
git push origin main  # 自动触发部署
```

---

## 🔧 服务管理命令

### 查看服务状态

```bash
# 查看后端日志
tail -f ~/AiChatBot/logs/backend.log

# 查看前端日志
tail -f ~/AiChatBot/logs/frontend.log

# 查看 nginx 日志
tail -f /usr/local/var/log/nginx/aichatbot-access.log
```

### 重启服务

```bash
# 重启后端
launchctl kickstart -k gui/$(id -u)/com.aichatbot.backend

# 重启前端
launchctl kickstart -k gui/$(id -u)/com.aichatbot.frontend

# 重启 nginx
brew services restart nginx
```

### 停止服务

```bash
# 停止后端
launchctl stop com.aichatbot.backend

# 停止前端
launchctl stop com.aichatbot.frontend

# 停止 nginx
brew services stop nginx
```

### 卸载服务

```bash
# 卸载 launchd 服务
launchctl unload ~/Library/LaunchAgents/com.aichatbot.backend.plist
launchctl unload ~/Library/LaunchAgents/com.aichatbot.frontend.plist
rm ~/Library/LaunchAgents/com.aichatbot.*

# 移除 nginx 配置
sudo rm /usr/local/etc/nginx/servers/nginx-aichatbot.conf
brew services restart nginx
```

---

## 🌐 访问地址

### 开发环境
- 前端：http://localhost:5173
- 后端：http://localhost:8000

### 生产环境（Mac mini）
- **直接访问**：
  - 前端：http://your-mac-mini-ip:3030
  - 后端：http://your-mac-mini-ip:8030

- **通过 Gateway（推荐）**：
  - 应用：http://your-mac-mini-ip
  - 后端 API：http://your-mac-mini-ip/api
  - 健康检查：http://your-mac-mini-ip/health

### 局域网访问
- 其他设备通过 Mac mini IP 访问
- 例如：http://192.168.1.100

---

## 🔐 环境变量配置

### 后端 (backend/.env)

```env
DEEPSEEK_API_KEY=your-api-key-here
DEEPSEEK_API_BASE=https://api.deepseek.com
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///./chat.db
```

### 前端

前端使用 Vite 环境变量（已自动配置）：
- `import.meta.env.PROD` - 生产环境标志
- 自动检测并使用正确的 API 地址

---

## 🐛 故障排查

### 问题 1: Backend 无法启动

```bash
# 查看错误日志
cat ~/AiChatBot/logs/backend.error.log

# 检查端口占用
lsof -i:8030

# 手动测试启动
cd ~/AiChatBot/backend
source .venv/bin/activate
uvicorn main:asgi_app --host 0.0.0.0 --port 8030
```

### 问题 2: Frontend 无法访问

```bash
# 查看错误日志
cat ~/AiChatBot/logs/frontend.error.log

# 检查 dist 目录是否存在
ls -la ~/AiChatBot/frontend/dist

# 重新构建
cd ~/AiChatBot/frontend
npm run build
```

### 问题 3: nginx 502 Bad Gateway

```bash
# 检查 nginx 错误日志
tail -f /usr/local/var/log/nginx/aichatbot-error.log

# 检查后端是否运行
curl http://localhost:8030/health

# 检查前端是否运行
curl http://localhost:3030

# 测试 nginx 配置
nginx -t

# 重启 nginx
brew services restart nginx
```

### 问题 4: Socket.IO 连接失败

```bash
# 检查 nginx 配置中的 /socket.io/ location
cat /usr/local/etc/nginx/servers/nginx-aichatbot.conf | grep -A 10 "location /socket.io"

# 确保 WebSocket 升级配置正确
# proxy_set_header Upgrade $http_upgrade;
# proxy_set_header Connection "upgrade";
```

### 问题 5: GitHub Actions 部署失败

- 检查 GitHub Actions 日志
- 验证 SSH 连接：`ssh user@mac-mini-ip`
- 确认 Secrets 配置正确
- 检查 Mac mini 的 SSH 服务是否开启

---

## 📊 监控和维护

### 检查服务状态

```bash
# 快速状态检查脚本
cat > ~/check-status.sh << 'EOF'
#!/bin/bash
echo "🔍 Service Status Check"
echo "======================"
echo ""
echo "Backend (8030):"
curl -s http://localhost:8030/health | python3 -m json.tool || echo "❌ Not responding"
echo ""
echo "Frontend (3030):"
curl -s -o /dev/null -w "%{http_code}" http://localhost:3030
echo ""
echo "Gateway (nginx):"
curl -s -o /dev/null -w "%{http_code}" http://localhost/health
echo ""
EOF

chmod +x ~/check-status.sh
./check-status.sh
```

### 数据库备份

```bash
# 备份数据库
cp ~/AiChatBot/backend/chat.db ~/AiChatBot/backups/chat-$(date +%Y%m%d).db

# 自动备份（添加到 crontab）
# 每天凌晨 2 点备份
# 0 2 * * * cp ~/AiChatBot/backend/chat.db ~/AiChatBot/backups/chat-$(date +\%Y\%m\%d).db
```

---

## 🔄 更新部署

### 自动更新（推荐）
```bash
# 推送到 GitHub main 分支，自动触发部署
git push origin main
```

### 手动更新
```bash
# 在 Mac mini 上
cd ~/AiChatBot
git pull origin main

# 重启服务
launchctl kickstart -k gui/$(id -u)/com.aichatbot.backend
launchctl kickstart -k gui/$(id -u)/com.aichatbot.frontend
```

---

## 📱 移动设备访问

从手机/平板访问（同一局域网）：
- 访问：http://your-mac-mini-ip
- 例如：http://192.168.1.100

---

## 🔒 安全建议

### 生产环境建议

1. **启用 HTTPS**
   ```bash
   # 使用 Let's Encrypt
   brew install certbot
   sudo certbot --nginx -d your-domain.com
   ```

2. **配置防火墙**
   ```bash
   # 只允许必要端口
   sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setglobalstate on
   ```

3. **设置强密码**
   - 修改 SECRET_KEY 为强随机字符串
   - 定期更换 API keys

4. **限制访问**
   - 在 nginx 中配置 IP 白名单
   - 或使用 VPN 访问

---

## 📞 支持

遇到问题：
- 查看日志文件：`~/AiChatBot/logs/`
- 查看 GitHub Issues
- 联系管理员

---

**部署完成后，你的 AI Group Chat 将 24/7 运行在 Mac mini 上！** 🎉
