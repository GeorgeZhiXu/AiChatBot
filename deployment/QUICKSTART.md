# 🚀 快速部署到 Mac Mini

## 一键安装（首次部署）

在 Mac mini 上执行：

```bash
# 1. 克隆代码
cd ~
git clone https://github.com/GeorgeZhiXu/AiChatBot.git
cd AiChatBot

# 2. 运行安装脚本
./deployment/setup.sh

# 3. 安装 nginx
brew install nginx

# 4. 配置 nginx
sudo cp deployment/nginx-aichatbot.conf /usr/local/etc/nginx/servers/
sudo nano /usr/local/etc/nginx/servers/nginx-aichatbot.conf
# 修改 server_name 为你的 Mac mini IP

# 5. 启动 nginx
nginx -t  # 测试配置
brew services start nginx

# 6. 访问应用
open http://your-mac-mini-ip
```

## GitHub 自动部署配置

### 1. 配置 SSH（在 Mac mini）

```bash
ssh-keygen -t ed25519 -C "github-actions"
cat ~/.ssh/id_ed25519.pub >> ~/.ssh/authorized_keys
sudo systemsetup -setremotelogin on
```

### 2. 在 GitHub 设置 Secrets

访问：https://github.com/GeorgeZhiXu/AiChatBot/settings/secrets/actions

添加：
- `MAC_MINI_HOST`: 你的 Mac mini IP（如 192.168.1.100）
- `MAC_MINI_USER`: 用户名（如 vivian）
- `MAC_MINI_SSH_KEY`: 复制 `cat ~/.ssh/id_ed25519` 的内容

### 3. 推送代码自动部署

```bash
git push origin main  # 自动触发部署
```

## 端口说明

- 前端：3030（内部）→ 80（nginx Gateway）
- 后端：8030（内部）→ 80/api（nginx Gateway）
- Socket.IO：8030/socket.io/（nginx Gateway）

## 常用命令

```bash
# 重启服务
launchctl kickstart -k gui/$(id -u)/com.aichatbot.backend
launchctl kickstart -k gui/$(id -u)/com.aichatbot.frontend

# 查看日志
tail -f ~/AiChatBot/logs/backend.log

# 检查状态
curl http://localhost:8030/health
```

完整文档：见 DEPLOYMENT.md
