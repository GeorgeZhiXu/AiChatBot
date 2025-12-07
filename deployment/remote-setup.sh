#!/bin/bash
# 远程配置 Mac mini 脚本
# 在当前开发机上运行，自动配置远程 Mac mini

set -e

MAC_MINI_IP="24.19.48.87"
MAC_MINI_USER="xuzhi"
DEEPSEEK_KEY="sk-d7eac45c7b224933bbdcf5280faa03fb"

echo "🚀 远程配置 Mac mini"
echo "===================="
echo ""
echo "目标: $MAC_MINI_USER@$MAC_MINI_IP"
echo ""

# 测试 SSH 连接
echo "🔍 测试 SSH 连接..."
if ! ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no "$MAC_MINI_USER@$MAC_MINI_IP" "echo 'Connection OK'" 2>/dev/null; then
    echo "❌ 无法连接到 Mac mini"
    echo ""
    echo "请确保："
    echo "1. Mac mini IP 正确: $MAC_MINI_IP"
    echo "2. 用户名正确: $MAC_MINI_USER"
    echo "3. Mac mini 已开启远程登录"
    echo "4. 你的 SSH 公钥已添加到 Mac mini"
    echo ""
    echo "手动测试: ssh $MAC_MINI_USER@$MAC_MINI_IP"
    exit 1
fi

echo "✅ SSH 连接成功"
echo ""

# 在 Mac mini 上执行完整配置
echo "📦 开始远程配置..."
ssh "$MAC_MINI_USER@$MAC_MINI_IP" bash << 'ENDSSH'
set -e

echo ""
echo "1️⃣  检查并启用远程登录..."
if ! sudo systemsetup -getremotelogin | grep -q "On"; then
    sudo systemsetup -setremotelogin on
fi
echo "✅ 远程登录已启用"

echo ""
echo "2️⃣  配置 SSH 密钥..."
SSH_KEY="$HOME/.ssh/id_ed25519"
if [ ! -f "$SSH_KEY" ]; then
    ssh-keygen -t ed25519 -C "github-actions" -f "$SSH_KEY" -N ""
    echo "✅ SSH 密钥已生成"
else
    echo "✅ SSH 密钥已存在"
fi

mkdir -p "$HOME/.ssh"
chmod 700 "$HOME/.ssh"
cat "$SSH_KEY.pub" >> "$HOME/.ssh/authorized_keys"
chmod 600 "$HOME/.ssh/authorized_keys"
sort -u "$HOME/.ssh/authorized_keys" -o "$HOME/.ssh/authorized_keys"
echo "✅ authorized_keys 已配置"

echo ""
echo "3️⃣  克隆代码..."
if [ -d "$HOME/AiChatBot" ]; then
    echo "⚠️  代码已存在，更新中..."
    cd "$HOME/AiChatBot"
    git fetch origin
    git reset --hard origin/main
else
    git clone https://github.com/GeorgeZhiXu/AiChatBot.git "$HOME/AiChatBot"
    cd "$HOME/AiChatBot"
fi
echo "✅ 代码已准备"

echo ""
echo "4️⃣  创建目录..."
mkdir -p logs backups
echo "✅ 目录已创建"

echo ""
echo "5️⃣  配置环境变量..."
SECRET_KEY=$(openssl rand -hex 32)
cat > backend/.env << EOF
DEEPSEEK_API_KEY=DEEPSEEK_KEY_PLACEHOLDER
DEEPSEEK_API_BASE=https://api.deepseek.com
SECRET_KEY=$SECRET_KEY
DATABASE_URL=sqlite:///./chat.db
EOF
echo "✅ .env 已创建"

echo ""
echo "6️⃣  安装后端依赖..."
cd backend
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi
source .venv/bin/activate
pip install -r requirements.txt --quiet
deactivate
echo "✅ 后端依赖已安装"

echo ""
echo "7️⃣  安装前端依赖..."
cd ../frontend
npm install --silent 2>&1 | grep -v "npm WARN" || true
echo "✅ 前端依赖已安装"

echo ""
echo "8️⃣  构建前端..."
npm run build 2>&1 | tail -1
echo "✅ 前端已构建"

echo ""
echo "9️⃣  安装 serve..."
npm list -g serve || npm install -g serve
echo "✅ serve 已安装"

echo ""
echo "🔟 配置 launchd 服务..."
cd ~/AiChatBot

# 更新 plist 文件
for plist in deployment/com.aichatbot.backend.plist deployment/com.aichatbot.frontend.plist; do
    sed -i '' "s|REPLACE_WITH_HOME|$HOME|g" "$plist"
done

# 读取并配置密钥
source backend/.env
sed -i '' "s|REPLACE_WITH_YOUR_API_KEY|DEEPSEEK_KEY_PLACEHOLDER|g" deployment/com.aichatbot.backend.plist
sed -i '' "s|REPLACE_WITH_YOUR_SECRET_KEY|$SECRET_KEY|g" deployment/com.aichatbot.backend.plist

# 安装服务
cp deployment/com.aichatbot.backend.plist ~/Library/LaunchAgents/
cp deployment/com.aichatbot.frontend.plist ~/Library/LaunchAgents/

# 重新加载
launchctl unload ~/Library/LaunchAgents/com.aichatbot.backend.plist 2>/dev/null || true
launchctl unload ~/Library/LaunchAgents/com.aichatbot.frontend.plist 2>/dev/null || true
launchctl load ~/Library/LaunchAgents/com.aichatbot.backend.plist
launchctl load ~/Library/LaunchAgents/com.aichatbot.frontend.plist
echo "✅ 服务已安装"

echo ""
echo "⏳ 等待服务启动..."
sleep 8

echo ""
echo "🔍 验证服务..."
curl -s http://localhost:8030/health && echo "✅ 后端运行中" || echo "⚠️ 后端未响应"
curl -s http://localhost:3030 > /dev/null && echo "✅ 前端运行中" || echo "⚠️ 前端未响应"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Mac mini 配置完成！"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "SSH 私钥内容（用于 GitHub Secrets）："
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
cat ~/.ssh/id_ed25519
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

ENDSSH

# 替换 API Key 占位符
echo ""
echo "🔑 配置 API Key..."
ssh "$MAC_MINI_USER@$MAC_MINI_IP" "sed -i '' 's|DEEPSEEK_KEY_PLACEHOLDER|$DEEPSEEK_KEY|g' ~/AiChatBot/backend/.env ~/AiChatBot/deployment/com.aichatbot.backend.plist && cp ~/AiChatBot/deployment/com.aichatbot.backend.plist ~/Library/LaunchAgents/ && launchctl kickstart -k gui/\$(id -u)/com.aichatbot.backend"

echo "✅ API Key 已配置并重启服务"

# 获取 SSH 私钥用于 GitHub Secrets
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 GitHub Secrets 配置"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "✅ MAC_MINI_HOST、MAC_MINI_USER、MAC_MINI_SSH_KEY 已配置"
echo ""
echo "如需查看 SSH 私钥（用于验证）："
echo "ssh $MAC_MINI_USER@$MAC_MINI_IP 'cat ~/.ssh/id_ed25519'"
echo ""

echo "🌐 下一步：配置 nginx"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "在 Mac mini 上执行："
echo ""
echo "ssh $MAC_MINI_USER@$MAC_MINI_IP"
echo "brew install nginx"
echo "sudo cp ~/AiChatBot/deployment/nginx-aichatbot.conf /usr/local/etc/nginx/servers/"
echo "nginx -t"
echo "brew services start nginx"
echo ""

echo "✅ 完成！"
echo ""
echo "访问: http://$MAC_MINI_IP"
echo ""
test
