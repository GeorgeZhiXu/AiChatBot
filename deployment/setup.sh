#!/bin/bash
# Setup script for Mac mini deployment
# Run this once on your Mac mini to configure services

set -e

echo "🚀 AI Group Chat - Mac Mini Setup Script"
echo "=========================================="
echo ""

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "❌ This script is designed for macOS (Mac mini)"
    exit 1
fi

# Get user home directory
USER_HOME="$HOME"
APP_DIR="$USER_HOME/AiChatBot"

echo "📁 App directory: $APP_DIR"
echo ""

# Step 1: Create logs directory
echo "📝 Creating logs directory..."
mkdir -p "$APP_DIR/logs"

# Step 2: Update launchd plist files with actual paths
echo "🔧 Configuring launchd services..."

for plist in "$APP_DIR/deployment/com.aichatbot.backend.plist" "$APP_DIR/deployment/com.aichatbot.frontend.plist"; do
    if [ -f "$plist" ]; then
        sed -i '' "s|REPLACE_WITH_HOME|$USER_HOME|g" "$plist"
        echo "  ✅ Updated: $(basename $plist)"
    fi
done

# Step 3: Prompt for API keys
echo ""
echo "🔑 Environment Configuration"
echo "----------------------------"
read -p "Enter your DeepSeek API Key: " DEEPSEEK_KEY
read -p "Enter a secret key for JWT (or press Enter for random): " SECRET_KEY

if [ -z "$SECRET_KEY" ]; then
    SECRET_KEY=$(openssl rand -hex 32)
    echo "Generated random secret key: $SECRET_KEY"
fi

# Update backend plist with API key
sed -i '' "s|REPLACE_WITH_YOUR_API_KEY|$DEEPSEEK_KEY|g" "$APP_DIR/deployment/com.aichatbot.backend.plist"
sed -i '' "s|REPLACE_WITH_YOUR_SECRET_KEY|$SECRET_KEY|g" "$APP_DIR/deployment/com.aichatbot.backend.plist"

# Also create .env file
cat > "$APP_DIR/backend/.env" <<EOF
DEEPSEEK_API_KEY=$DEEPSEEK_KEY
DEEPSEEK_API_BASE=https://api.deepseek.com
SECRET_KEY=$SECRET_KEY
DATABASE_URL=sqlite:///./chat.db
EOF

echo "  ✅ Created backend/.env"

# Step 4: Install backend dependencies
echo ""
echo "📦 Installing backend dependencies..."
cd "$APP_DIR/backend"
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi
source .venv/bin/activate
pip install -r requirements.txt --quiet
echo "  ✅ Backend dependencies installed"

# Step 5: Install frontend dependencies
echo ""
echo "🎨 Installing frontend dependencies..."
cd "$APP_DIR/frontend"
npm install --silent
echo "  ✅ Frontend dependencies installed"

# Step 6: Build frontend for production
echo ""
echo "🏗️  Building frontend for production..."
npm run build
echo "  ✅ Frontend built successfully"

# Step 7: Install npm serve globally (for serving frontend)
echo ""
echo "📦 Installing npm serve..."
npm install -g serve
echo "  ✅ serve installed"

# Step 8: Copy launchd plists to LaunchAgents
echo ""
echo "🔧 Installing launchd services..."
cp "$APP_DIR/deployment/com.aichatbot.backend.plist" "$USER_HOME/Library/LaunchAgents/"
cp "$APP_DIR/deployment/com.aichatbot.frontend.plist" "$USER_HOME/Library/LaunchAgents/"
echo "  ✅ Services installed"

# Step 9: Load and start services
echo ""
echo "▶️  Starting services..."
launchctl load "$USER_HOME/Library/LaunchAgents/com.aichatbot.backend.plist"
launchctl load "$USER_HOME/Library/LaunchAgents/com.aichatbot.frontend.plist"
echo "  ✅ Services started"

# Step 10: Wait and check status
echo ""
echo "⏳ Waiting for services to start..."
sleep 5

echo ""
echo "🔍 Checking service status..."
if curl -s http://localhost:8030/health > /dev/null; then
    echo "  ✅ Backend: http://localhost:8030 (running)"
else
    echo "  ⚠️  Backend: Not responding"
fi

if curl -s http://localhost:3030 > /dev/null; then
    echo "  ✅ Frontend: http://localhost:3030 (running)"
else
    echo "  ⚠️  Frontend: Not responding"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Install nginx: brew install nginx"
echo "2. Configure nginx:"
echo "   cp $APP_DIR/deployment/nginx-aichatbot.conf /usr/local/etc/nginx/servers/"
echo "   Edit the file and replace 'your-mac-mini.local' with your actual hostname/IP"
echo "3. Start nginx: brew services start nginx"
echo "4. Access via Gateway: http://your-mac-mini.local"
echo ""
echo "🔧 Useful commands:"
echo "  View logs: tail -f ~/AiChatBot/logs/backend.log"
echo "  Restart backend: launchctl kickstart -k gui/\$(id -u)/com.aichatbot.backend"
echo "  Restart frontend: launchctl kickstart -k gui/\$(id -u)/com.aichatbot.frontend"
echo "  Stop services: launchctl unload ~/Library/LaunchAgents/com.aichatbot.*"
echo ""
