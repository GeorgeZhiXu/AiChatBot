#!/bin/bash

# AiChatBot PM2 Deployment Script
# This script deploys AiChatBot to /Users/xuzhi/prod/aichatbot with PM2

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PROD_DIR="/Users/xuzhi/prod/aichatbot"
GATEWAY_DIR="/Users/xuzhi/prod/gateway"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_info() {
    echo -e "${YELLOW}[i]${NC} $1"
}

# Check if running on Mac mini
if [[ ! -d "$GATEWAY_DIR" ]]; then
    print_error "Gateway directory not found. This script should run on the Mac mini."
    exit 1
fi

print_info "Starting AiChatBot PM2 deployment..."

# Create directory structure
print_info "Creating directory structure..."
mkdir -p "$PROD_DIR"/{backend,frontend,logs,backups}

# Backup existing deployment
if [[ -d "$PROD_DIR/backend" ]] && [[ -n "$(ls -A "$PROD_DIR/backend" 2>/dev/null)" ]]; then
    print_info "Creating backup..."
    BACKUP_NAME="aichatbot-backup-$(date +%Y%m%d-%H%M%S).tar.gz"
    tar -czf "$PROD_DIR/backups/$BACKUP_NAME" \
        -C "$PROD_DIR" backend frontend 2>/dev/null || true
    print_status "Backup created: $BACKUP_NAME"
fi

# Copy backend files
print_info "Deploying backend..."
rsync -av --delete \
    --exclude='.venv' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='*.db' \
    --exclude='.env' \
    "$PROJECT_ROOT/backend/" "$PROD_DIR/backend/"

# Preserve .env if exists, otherwise copy from example
if [[ ! -f "$PROD_DIR/backend/.env" ]]; then
    print_info "Creating .env file..."
    if [[ -f "$PROD_DIR/backend/.env.example" ]]; then
        cp "$PROD_DIR/backend/.env.example" "$PROD_DIR/backend/.env"
        print_error "Please edit $PROD_DIR/backend/.env with your API keys"
        exit 1
    fi
fi

# Setup Python virtual environment
print_info "Setting up Python virtual environment..."
if [[ ! -d "$PROD_DIR/backend/.venv" ]]; then
    cd "$PROD_DIR/backend"
    python3 -m venv .venv
fi

# Install Python dependencies
print_info "Installing Python dependencies..."
cd "$PROD_DIR/backend"
source .venv/bin/activate
pip install -q --upgrade pip
pip install -q -r requirements.txt
deactivate

# Build frontend
print_info "Building frontend..."
cd "$PROJECT_ROOT/frontend"
npm install
npm run build

# Deploy frontend build
print_info "Deploying frontend..."
rsync -av --delete "$PROJECT_ROOT/frontend/dist/" "$PROD_DIR/frontend/dist/"

# Copy ecosystem config
print_info "Copying PM2 ecosystem config..."
cp "$PROJECT_ROOT/ecosystem.config.js" "$PROD_DIR/"

# Install serve globally if not present
if ! command -v serve &> /dev/null; then
    print_info "Installing serve globally..."
    npm install -g serve
fi

# Update gateway nginx configuration
print_info "Updating gateway nginx configuration..."
NGINX_CONFIG="$GATEWAY_DIR/config/nginx.conf"

if ! grep -q "location /aichatbot/" "$NGINX_CONFIG" 2>/dev/null; then
    print_info "Adding AiChatBot route to nginx config..."

    # Create backup of nginx config
    cp "$NGINX_CONFIG" "$NGINX_CONFIG.backup-$(date +%Y%m%d-%H%M%S)"

    # Add AiChatBot configuration before the health check endpoint
    awk '/location \/health/ && !done {
        print "        # AiChatBot - AI Group Chat (token auth required)"
        print "        location /aichatbot/ {"
        print "            # Token authentication"
        print "            auth_request /auth;"
        print ""
        print "            # Redirect to login if not authenticated"
        print "            error_page 401 = @auth_redirect;"
        print ""
        print "            rewrite ^/aichatbot/(.*)$ /$1 break;"
        print ""
        print "            proxy_pass http://127.0.0.1:3030;"
        print "            proxy_set_header Host $host;"
        print "            proxy_set_header X-Real-IP $remote_addr;"
        print "            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;"
        print "            proxy_set_header X-Forwarded-Proto $scheme;"
        print "            proxy_set_header X-Forwarded-Host $host;"
        print ""
        print "            # WebSocket support for Socket.IO"
        print "            proxy_http_version 1.1;"
        print "            proxy_set_header Upgrade $http_upgrade;"
        print "            proxy_set_header Connection \"upgrade\";"
        print ""
        print "            # Timeouts"
        print "            proxy_connect_timeout 60s;"
        print "            proxy_send_timeout 60s;"
        print "            proxy_read_timeout 60s;"
        print "        }"
        print ""
        print "        # AiChatBot Backend API (token auth required)"
        print "        location /aichatbot-api/ {"
        print "            # Token authentication"
        print "            auth_request /auth;"
        print ""
        print "            # Redirect to login if not authenticated"
        print "            error_page 401 = @auth_redirect;"
        print ""
        print "            rewrite ^/aichatbot-api/(.*)$ /$1 break;"
        print ""
        print "            proxy_pass http://127.0.0.1:8030;"
        print "            proxy_set_header Host $host;"
        print "            proxy_set_header X-Real-IP $remote_addr;"
        print "            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;"
        print "            proxy_set_header X-Forwarded-Proto $scheme;"
        print ""
        print "            # WebSocket support for Socket.IO"
        print "            proxy_http_version 1.1;"
        print "            proxy_set_header Upgrade $http_upgrade;"
        print "            proxy_set_header Connection \"upgrade\";"
        print ""
        print "            # Rate limiting for API"
        print "            limit_req zone=api burst=50 nodelay;"
        print "        }"
        print ""
        done=1
    }
    { print }' "$NGINX_CONFIG" > "$NGINX_CONFIG.tmp"

    mv "$NGINX_CONFIG.tmp" "$NGINX_CONFIG"
    print_status "AiChatBot routes added to nginx config"
else
    print_status "AiChatBot routes already exist in nginx config"
fi

# Test nginx configuration
print_info "Testing nginx configuration..."
if nginx -t -c "$NGINX_CONFIG" 2>&1 | grep -q "successful"; then
    print_status "Nginx configuration is valid"

    # Reload nginx if it's running
    if pgrep -x nginx > /dev/null; then
        print_info "Reloading nginx..."
        nginx -s reload -c "$NGINX_CONFIG"
        print_status "Nginx reloaded"
    fi
else
    print_error "Nginx configuration test failed"
    print_info "Restoring backup..."
    mv "$NGINX_CONFIG.backup-$(date +%Y%m%d)-"* "$NGINX_CONFIG" 2>/dev/null || true
    exit 1
fi

# Start or restart PM2 applications
print_info "Managing PM2 processes..."
cd "$PROD_DIR"

# Check if PM2 is running these apps
if pm2 list | grep -q "aichatbot-backend\|aichatbot-frontend"; then
    print_info "Restarting existing PM2 processes..."
    pm2 restart ecosystem.config.js
else
    print_info "Starting PM2 processes..."
    pm2 start ecosystem.config.js
fi

# Save PM2 configuration
pm2 save

# Setup PM2 startup script if not already done
if ! pm2 startup | grep -q "already"; then
    print_info "Setting up PM2 startup script..."
    pm2 startup launchd -u "$(whoami)" --hp "$HOME" | tail -n 1 | bash
fi

# Verify deployment
print_info "Verifying deployment..."
sleep 3

# Check backend
if curl -s http://localhost:8030/health > /dev/null; then
    print_status "Backend is responding on port 8030"
else
    print_error "Backend health check failed"
fi

# Check frontend
if curl -s http://localhost:3030 > /dev/null; then
    print_status "Frontend is responding on port 3030"
else
    print_error "Frontend health check failed"
fi

# Display PM2 status
echo ""
print_info "PM2 Process Status:"
pm2 list | grep "aichatbot"

echo ""
print_status "Deployment completed successfully!"
echo ""
print_info "Access URLs:"
echo "  - Frontend:  http://localhost:3030"
echo "  - Backend:   http://localhost:8030"
echo "  - Gateway:   http://localhost/aichatbot/"
echo "  - API:       http://localhost/aichatbot-api/"
echo ""
print_info "Management commands:"
echo "  - View logs:     pm2 logs aichatbot"
echo "  - Restart:       pm2 restart aichatbot-backend aichatbot-frontend"
echo "  - Stop:          pm2 stop aichatbot-backend aichatbot-frontend"
echo "  - Status:        pm2 list"
echo ""
