#!/bin/bash
# Mac mini 自动配置脚本
# 在 Mac mini (24.19.48.87) 上运行此脚本

set -e

echo "🚀 AI Group Chat - Mac mini 自动配置脚本"
echo "=========================================="
echo ""
echo "本脚本将配置："
echo "  1. SSH 远程登录"
echo "  2. SSH 密钥生成"
echo "  3. 克隆 GitHub 代码"
echo "  4. 安装依赖"
echo "  5. 配置环境变量"
echo ""
read -p "按回车继续... " -r

# 获取当前用户
CURRENT_USER=$(whoami)
USER_HOME="$HOME"
APP_DIR="$USER_HOME/AiChatBot"

echo ""
echo "✅ 当前用户: $CURRENT_USER"
echo "✅ 应用目录: $APP_DIR"
echo ""

# 步骤 1: 启用远程登录
echo "1️⃣  配置 SSH 远程登录..."
if sudo systemsetup -getremotelogin | grep -q "On"; then
    echo "  ✅ 远程登录已启用"
else
    echo "  🔧 启用远程登录..."
    sudo systemsetup -setremotelogin on
    echo "  ✅ 远程登录已启用"
fi

# 步骤 2: 生成 SSH 密钥
echo ""
echo "2️⃣  配置 SSH 密钥..."

SSH_KEY="$USER_HOME/.ssh/id_ed25519"
if [ -f "$SSH_KEY" ]; then
    echo "  ✅ SSH 密钥已存在: $SSH_KEY"
else
    echo "  🔧 生成新的 SSH 密钥..."
    ssh-keygen -t ed25519 -C "github-actions" -f "$SSH_KEY" -N ""
    echo "  ✅ SSH 密钥已生成"
fi

# 添加公钥到 authorized_keys
echo "  🔧 配置 authorized_keys..."
mkdir -p "$USER_HOME/.ssh"
chmod 700 "$USER_HOME/.ssh"
cat "$SSH_KEY.pub" >> "$USER_HOME/.ssh/authorized_keys"
chmod 600 "$USER_HOME/.ssh/authorized_keys"
# 去重
sort -u "$USER_HOME/.ssh/authorized_keys" -o "$USER_HOME/.ssh/authorized_keys"
echo "  ✅ authorized_keys 已配置"

# 步骤 3: 克隆代码
echo ""
echo "3️⃣  克隆 GitHub 代码..."

if [ -d "$APP_DIR" ]; then
    echo "  ⚠️  目录已存在: $APP_DIR"
    read -p "是否删除并重新克隆？(y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf "$APP_DIR"
        git clone https://github.com/GeorgeZhiXu/AiChatBot.git "$APP_DIR"
        echo "  ✅ 代码已重新克隆"
    else
        echo "  ⏭️  跳过克隆，使用现有代码"
        cd "$APP_DIR"
        git pull origin main
        echo "  ✅ 代码已更新"
    fi
else
    git clone https://github.com/GeorgeZhiXu/AiChatBot.git "$APP_DIR"
    echo "  ✅ 代码已克隆"
fi

cd "$APP_DIR"

# 步骤 4: 检查依赖
echo ""
echo "4️⃣  检查系统依赖..."

# 检查 Python
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo "  ✅ Python: $PYTHON_VERSION"
else
    echo "  ❌ Python 未安装，请安装 Python 3.12+"
    exit 1
fi

# 检查 Node.js
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo "  ✅ Node.js: $NODE_VERSION"
else
    echo "  ❌ Node.js 未安装，请安装 Node.js 16+"
    exit 1
fi

# 检查 Homebrew
if command -v brew &> /dev/null; then
    echo "  ✅ Homebrew: $(brew --version | head -1)"
else
    echo "  ⚠️  Homebrew 未安装（安装 nginx 时需要）"
    echo "  安装命令: /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
fi

# 步骤 5: 创建必要目录
echo ""
echo "5️⃣  创建必要目录..."
mkdir -p "$APP_DIR/logs"
mkdir -p "$APP_DIR/backups"
echo "  ✅ 目录已创建"

# 步骤 6: 配置环境变量
echo ""
echo "6️⃣  配置环境变量..."

if [ -f "$APP_DIR/backend/.env" ]; then
    echo "  ⚠️  .env 文件已存在"
    read -p "是否重新配置？(y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "  ⏭️  跳过环境变量配置"
    else
        rm "$APP_DIR/backend/.env"
    fi
fi

if [ ! -f "$APP_DIR/backend/.env" ]; then
    echo "  请输入 DeepSeek API Key:"
    read -r DEEPSEEK_KEY

    echo "  生成 JWT Secret Key..."
    SECRET_KEY=$(openssl rand -hex 32)

    cat > "$APP_DIR/backend/.env" <<EOF
DEEPSEEK_API_KEY=$DEEPSEEK_KEY
DEEPSEEK_API_BASE=https://api.deepseek.com
SECRET_KEY=$SECRET_KEY
DATABASE_URL=sqlite:///./chat.db
EOF
    echo "  ✅ .env 文件已创建"
    echo "  JWT Secret: $SECRET_KEY"
fi

# 步骤 7: 安装后端依赖
echo ""
echo "7️⃣  安装后端依赖..."
cd "$APP_DIR/backend"

if [ ! -d ".venv" ]; then
    echo "  🔧 创建虚拟环境..."
    python3 -m venv .venv
fi

echo "  🔧 安装 Python 依赖..."
source .venv/bin/activate
pip install -r requirements.txt --quiet
echo "  ✅ 后端依赖已安装"

# 步骤 8: 安装前端依赖
echo ""
echo "8️⃣  安装前端依赖..."
cd "$APP_DIR/frontend"

echo "  🔧 安装 Node 依赖..."
npm install --silent
echo "  ✅ 前端依赖已安装"

# 步骤 9: 构建前端
echo ""
echo "9️⃣  构建前端生产版本..."
npm run build
echo "  ✅ 前端已构建: $APP_DIR/frontend/dist"

# 步骤 10: 安装 serve
echo ""
echo "🔟 安装 npm serve（用于服务前端）..."
npm install -g serve
echo "  ✅ serve 已安装"

# 步骤 11: 配置 launchd 服务
echo ""
echo "1️⃣1️⃣  配置 launchd 自启动服务..."

# 更新 plist 文件中的路径和密钥
for plist in "$APP_DIR/deployment/com.aichatbot.backend.plist" "$APP_DIR/deployment/com.aichatbot.frontend.plist"; do
    if [ -f "$plist" ]; then
        # 替换路径
        sed -i '' "s|REPLACE_WITH_HOME|$USER_HOME|g" "$plist"
        echo "  ✅ 已配置: $(basename $plist)"
    fi
done

# 从 .env 读取密钥
if [ -f "$APP_DIR/backend/.env" ]; then
    source "$APP_DIR/backend/.env"
    sed -i '' "s|REPLACE_WITH_YOUR_API_KEY|$DEEPSEEK_API_KEY|g" "$APP_DIR/deployment/com.aichatbot.backend.plist"
    sed -i '' "s|REPLACE_WITH_YOUR_SECRET_KEY|$SECRET_KEY|g" "$APP_DIR/deployment/com.aichatbot.backend.plist"
fi

# 复制到 LaunchAgents
echo "  🔧 安装 launchd 服务..."
cp "$APP_DIR/deployment/com.aichatbot.backend.plist" "$USER_HOME/Library/LaunchAgents/"
cp "$APP_DIR/deployment/com.aichatbot.frontend.plist" "$USER_HOME/Library/LaunchAgents/"

# 卸载旧服务（如果存在）
launchctl unload "$USER_HOME/Library/LaunchAgents/com.aichatbot.backend.plist" 2>/dev/null || true
launchctl unload "$USER_HOME/Library/LaunchAgents/com.aichatbot.frontend.plist" 2>/dev/null || true

# 加载新服务
launchctl load "$USER_HOME/Library/LaunchAgents/com.aichatbot.backend.plist"
launchctl load "$USER_HOME/Library/LaunchAgents/com.aichatbot.frontend.plist"

echo "  ✅ launchd 服务已安装并启动"

# 步骤 12: 等待服务启动
echo ""
echo "⏳ 等待服务启动（10秒）..."
sleep 10

# 步骤 13: 验证服务
echo ""
echo "🔍 验证服务状态..."

if curl -s http://localhost:8030/health > /dev/null 2>&1; then
    echo "  ✅ 后端运行中: http://localhost:8030"
else
    echo "  ⚠️  后端未响应，请检查日志: tail -f ~/AiChatBot/logs/backend.log"
fi

if curl -s http://localhost:3030 > /dev/null 2>&1; then
    echo "  ✅ 前端运行中: http://localhost:3030"
else
    echo "  ⚠️  前端未响应，请检查日志: tail -f ~/AiChatBot/logs/frontend.log"
fi

# 步骤 14: 显示 GitHub Secrets 配置信息
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 GitHub Secrets 配置信息"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "请访问: https://github.com/GeorgeZhiXu/AiChatBot/settings/secrets/actions"
echo ""
echo "添加以下 Secrets："
echo ""
echo "1️⃣  MAC_MINI_HOST"
echo "   值: 24.19.48.87"
echo ""
echo "2️⃣  MAC_MINI_USER"
echo "   值: $CURRENT_USER"
echo ""
echo "3️⃣  MAC_MINI_SSH_KEY"
echo "   值: (复制以下内容)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
cat "$SSH_KEY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 步骤 15: nginx 安装提示
echo ""
echo "🌐 下一步：安装 nginx Gateway"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "执行以下命令："
echo ""
echo "  # 安装 nginx"
echo "  brew install nginx"
echo ""
echo "  # 配置 nginx"
echo "  sudo cp ~/AiChatBot/deployment/nginx-aichatbot.conf /usr/local/etc/nginx/servers/"
echo ""
echo "  # 测试配置"
echo "  nginx -t"
echo ""
echo "  # 启动 nginx"
echo "  brew services start nginx"
echo ""

# 步骤 16: 测试命令
echo "🔧 常用管理命令："
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "# 查看日志"
echo "tail -f ~/AiChatBot/logs/backend.log"
echo "tail -f ~/AiChatBot/logs/frontend.log"
echo ""
echo "# 重启服务"
echo "launchctl kickstart -k gui/\$(id -u)/com.aichatbot.backend"
echo "launchctl kickstart -k gui/\$(id -u)/com.aichatbot.frontend"
echo ""
echo "# 停止服务"
echo "launchctl stop com.aichatbot.backend"
echo "launchctl stop com.aichatbot.frontend"
echo ""

echo "✅ Mac mini 配置完成！"
echo ""
echo "📱 访问应用: http://24.19.48.87"
echo ""
