# 🚀 AiChatBot Complete Deployment Guide

Comprehensive guide for deploying AiChatBot to Mac mini with PM2 process management, nginx gateway integration, and automated GitHub Actions CI/CD.

---

## 📋 Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Prerequisites](#prerequisites)
3. [Initial Setup](#initial-setup)
4. [GitHub Actions Setup](#github-actions-setup)
5. [PM2 Configuration](#pm2-configuration)
6. [Nginx Gateway Configuration](#nginx-gateway-configuration)
7. [Deployment Process](#deployment-process)
8. [Management Commands](#management-commands)
9. [Troubleshooting](#troubleshooting)
10. [Monitoring & Maintenance](#monitoring--maintenance)
11. [Security Considerations](#security-considerations)

---

## 🏗️ Architecture Overview

### System Architecture

```
Internet/LAN (Port 80)
       ↓
┌─────────────────────────────────────────┐
│  Nginx Gateway                          │
│  /Users/xuzhi/prod/gateway              │
│                                         │
│  Routes:                                │
│  • /                  → Dashboard       │
│  • /whiteboard/       → Whiteboard app  │
│  • /tingxie/          → TingXie app     │
│  • /aichatbot/        → AiChatBot UI    │
│  • /aichatbot-api/    → AiChatBot API   │
└─────────────────────────────────────────┘
              ↓
    ┌─────────────────┐
    │   PM2 Manager   │
    └─────────────────┘
         ↓         ↓
    Frontend    Backend
   (Port 3030) (Port 8030)
```

### Directory Structure

```
/Users/xuzhi/
├── AiChatBot/                      # Git repository (source code)
│   ├── .github/workflows/
│   │   ├── deploy-pm2.yml         # GitHub Actions workflow
│   │   └── deploy.yml             # Legacy (disabled)
│   ├── backend/
│   │   ├── main.py
│   │   ├── requirements.txt
│   │   └── .env                   # Local dev only (not committed)
│   ├── frontend/
│   │   ├── src/
│   │   ├── vite.config.js
│   │   └── package.json
│   ├── deployment/
│   │   └── deploy-pm2.sh          # Deployment script
│   ├── ecosystem.config.js        # PM2 configuration
│   ├── DEPLOYMENT_GUIDE.md        # This file
│   ├── DEPLOYMENT_PM2.md          # PM2-specific docs
│   └── GITHUB_SECRETS.md          # Secrets setup guide
│
└── prod/
    ├── gateway/                    # Nginx gateway
    │   ├── config/nginx.conf      # Main nginx config
    │   ├── logs/
    │   ├── www/
    │   └── scripts/
    │
    └── aichatbot/                  # Production deployment
        ├── backend/
        │   ├── .venv/             # Python virtual environment
        │   ├── .env               # Production secrets (auto-generated)
        │   ├── main.py
        │   └── chat.db            # SQLite database
        ├── frontend/
        │   └── dist/              # Built React app
        ├── logs/
        │   ├── backend-error.log
        │   ├── backend-out.log
        │   ├── frontend-error.log
        │   └── frontend-out.log
        ├── backups/               # Deployment backups
        └── ecosystem.config.js    # PM2 config (with secrets)
```

### Port Configuration

| Service | Port | Protocol | Access |
|---------|------|----------|--------|
| Nginx Gateway | 80 | HTTP | External (0.0.0.0) |
| Frontend (serve) | 3030 | HTTP | Internal (127.0.0.1) |
| Backend (uvicorn) | 8030 | HTTP/WS | Internal (127.0.0.1) |

### Service URLs

**External Access (via Gateway):**
- Dashboard: `http://24.19.48.87/`
- AiChatBot UI: `http://24.19.48.87/aichatbot/`
- Backend API: `http://24.19.48.87/aichatbot-api/`
- Health Check: `http://24.19.48.87/health` (no auth)

**Direct Access (Internal):**
- Frontend: `http://localhost:3030`
- Backend: `http://localhost:8030`
- Backend Health: `http://localhost:8030/health`

---

## 📦 Prerequisites

### On Mac Mini

1. **Operating System**: macOS 12.0+ (already running)
2. **Homebrew**: Package manager
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

3. **Git**: Version control (usually pre-installed)
   ```bash
   git --version
   ```

4. **Python 3.12+**:
   ```bash
   brew install python@3.12
   python3 --version
   ```

5. **Node.js 16+**:
   ```bash
   brew install node
   node --version
   npm --version
   ```

6. **PM2**: Process manager
   ```bash
   npm install -g pm2
   pm2 --version
   ```

7. **Nginx**: Already configured at `/Users/xuzhi/prod/gateway`

### On Development Machine

1. **Git**: To push code changes
2. **GitHub CLI** (optional): For managing secrets
   ```bash
   brew install gh
   gh auth login
   ```

---

## 🚀 Initial Setup

### Step 1: Clone Repository on Mac Mini

```bash
# SSH into your Mac mini
ssh xuzhi@24.19.48.87

# Clone the repository
cd ~
git clone https://github.com/GeorgeZhiXu/AiChatBot.git
cd AiChatBot
```

### Step 2: Run Initial Deployment

```bash
cd ~/AiChatBot

# Make deployment script executable
chmod +x deployment/deploy-pm2.sh

# Run deployment
./deployment/deploy-pm2.sh
```

The script will:
- ✅ Create `/Users/xuzhi/prod/aichatbot/` directory structure
- ✅ Copy application files to production directory
- ✅ Setup Python virtual environment
- ✅ Install Python dependencies
- ✅ Build frontend production bundle
- ✅ Configure nginx gateway routes
- ✅ Start PM2 processes
- ✅ Verify deployment

### Step 3: Configure Secrets

If running manually (not using GitHub Secrets), edit the `.env` file:

```bash
nano /Users/xuzhi/prod/aichatbot/backend/.env
```

Add your secrets:
```env
DEEPSEEK_API_KEY=sk-your-api-key-here
DEEPSEEK_API_BASE=https://api.deepseek.com
SECRET_KEY=your-jwt-secret-here
DATABASE_URL=sqlite:///./chat.db
```

Then restart the backend:
```bash
pm2 restart aichatbot-backend
```

---

## 🔐 GitHub Actions Setup

### Overview

The GitHub Actions workflow (`deploy-pm2.yml`) automatically deploys your application whenever you push to the `main` branch.

### Required GitHub Secrets

Go to: `https://github.com/GeorgeZhiXu/AiChatBot/settings/secrets/actions`

#### SSH Connection Secrets

| Secret Name | Description | How to Get |
|-------------|-------------|------------|
| `MAC_MINI_HOST` | IP address or hostname | `24.19.48.87` or `xuzhi.ddns.net` |
| `MAC_MINI_USER` | Username on Mac mini | `xuzhi` |
| `MAC_MINI_SSH_KEY` | SSH private key | See below |
| `MAC_MINI_SSH_PORT` | SSH port (optional) | `22` |

#### Application Secrets

| Secret Name | Description | How to Get |
|-------------|-------------|------------|
| `DEEPSEEK_API_KEY` | DeepSeek API key | https://platform.deepseek.com |
| `SECRET_KEY` | JWT secret for auth | `openssl rand -hex 32` |

### Generate SSH Key Pair

On your Mac mini:

```bash
# Generate SSH key
ssh-keygen -t ed25519 -C "github-actions-aichatbot" -f ~/.ssh/aichatbot_deploy

# Add public key to authorized_keys
cat ~/.ssh/aichatbot_deploy.pub >> ~/.ssh/authorized_keys

# Display private key (copy this for GitHub secret)
cat ~/.ssh/aichatbot_deploy
```

Copy the entire output including `-----BEGIN` and `-----END` lines.

### Set GitHub Secrets via CLI

Using GitHub CLI:

```bash
# SSH secrets
gh secret set MAC_MINI_HOST --body "24.19.48.87" --repo GeorgeZhiXu/AiChatBot
gh secret set MAC_MINI_USER --body "xuzhi" --repo GeorgeZhiXu/AiChatBot
gh secret set MAC_MINI_SSH_KEY --body "$(cat ~/.ssh/aichatbot_deploy)" --repo GeorgeZhiXu/AiChatBot

# Application secrets
gh secret set DEEPSEEK_API_KEY --body "sk-your-key-here" --repo GeorgeZhiXu/AiChatBot
gh secret set SECRET_KEY --body "$(openssl rand -hex 32)" --repo GeorgeZhiXu/AiChatBot
```

### Verify Secrets

```bash
gh secret list --repo GeorgeZhiXu/AiChatBot
```

Expected output:
```
DEEPSEEK_API_KEY  Updated 2025-12-08
MAC_MINI_HOST     Updated 2025-12-08
MAC_MINI_SSH_KEY  Updated 2025-12-07
MAC_MINI_USER     Updated 2025-12-07
SECRET_KEY        Updated 2025-12-08
```

### Workflow Behavior

**Automatic Deployment:**
```bash
git add .
git commit -m "your changes"
git push origin main
```

**Manual Deployment:**
- Go to: https://github.com/GeorgeZhiXu/AiChatBot/actions
- Select "Deploy to Mac Mini (PM2 + Gateway)"
- Click "Run workflow"

**Workflow Steps:**
1. Checkout code
2. SSH into Mac mini
3. Pull latest code
4. Create/update `.env` from GitHub Secrets
5. Run `deploy-pm2.sh` script
6. Build frontend
7. Restart PM2 processes
8. Verify health checks
9. Display deployment summary

---

## ⚙️ PM2 Configuration

### Ecosystem File

Location: `/Users/xuzhi/prod/aichatbot/ecosystem.config.js`

```javascript
module.exports = {
  apps: [
    {
      name: 'aichatbot-backend',
      cwd: '/Users/xuzhi/prod/aichatbot/backend',
      script: '/Users/xuzhi/prod/aichatbot/backend/.venv/bin/uvicorn',
      args: 'main:asgi_app --host 0.0.0.0 --port 8030',
      interpreter: 'none',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '500M',
      env: {
        PYTHONPATH: '/Users/xuzhi/prod/aichatbot/backend',
        PATH: '/Users/xuzhi/prod/aichatbot/backend/.venv/bin:/usr/local/bin:/usr/bin:/bin',
        DEEPSEEK_API_KEY: 'your-key',
        SECRET_KEY: 'your-secret',
        DATABASE_URL: 'sqlite:///./chat.db'
      }
    },
    {
      name: 'aichatbot-frontend',
      cwd: '/Users/xuzhi/prod/aichatbot/frontend',
      script: 'npx',
      args: 'serve -s dist -l 3030',
      interpreter: 'none',
      instances: 1,
      autorestart: true,
      max_memory_restart: '300M'
    }
  ]
};
```

### PM2 Key Features

**Auto-restart:**
- Services automatically restart on crash
- Max 10 restart attempts within 10 seconds
- Memory limit: 500MB (backend), 300MB (frontend)

**Log Management:**
- Auto-rotating logs
- Separate error and output logs
- Timestamped entries
- Location: `/Users/xuzhi/prod/aichatbot/logs/`

**Persistence:**
- PM2 saves process list on changes
- Configured for auto-start on system boot (via launchd)

### PM2 Startup Configuration

To enable PM2 auto-start on Mac mini boot (one-time setup):

```bash
# Generate startup script
pm2 startup launchd

# Copy and run the command it outputs (requires sudo)
# Example: sudo env PATH=$PATH:/usr/bin pm2 startup launchd -u xuzhi --hp /Users/xuzhi

# Save current process list
pm2 save
```

---

## 🌐 Nginx Gateway Configuration

### Gateway Location

**Config file**: `/Users/xuzhi/prod/gateway/config/nginx.conf`

### AiChatBot Routes

The deployment script automatically adds these routes:

#### 1. Frontend Route (`/aichatbot/`)

```nginx
# AiChatBot - AI Group Chat (token auth required)
location /aichatbot/ {
    # Token authentication via gateway
    auth_request /auth;
    error_page 401 = @auth_redirect;

    # Proxy to frontend (preserve path)
    proxy_pass http://127.0.0.1:3030;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;

    # WebSocket support
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";

    # Timeouts
    proxy_connect_timeout 60s;
    proxy_send_timeout 60s;
    proxy_read_timeout 60s;
}
```

#### 2. Static Assets Route (`/aichatbot/assets/`)

```nginx
# AiChatBot static assets (no auth required for CSS/JS)
location /aichatbot/assets/ {
    rewrite ^/aichatbot/(.*)$ /$1 break;
    proxy_pass http://127.0.0.1:3030;
    proxy_set_header Host $host;
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

#### 3. Socket.IO Route (`/aichatbot-api/socket.io/`)

```nginx
# AiChatBot Socket.IO (no auth required)
location /aichatbot-api/socket.io/ {
    rewrite ^/aichatbot-api/(.*)$ /$1 break;
    proxy_pass http://127.0.0.1:8030;
    proxy_set_header Host $host;

    # WebSocket support
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";

    # Long-lived connection timeouts
    proxy_connect_timeout 60s;
    proxy_send_timeout 60s;
    proxy_read_timeout 300s;
}
```

#### 4. Public Auth Routes (`/aichatbot-api/auth/*`)

```nginx
# AiChatBot public auth endpoints (no auth required)
location ~ ^/aichatbot-api/(auth|health) {
    rewrite ^/aichatbot-api/(.*)$ /api/$1 break;
    proxy_pass http://127.0.0.1:8030;
    proxy_set_header Host $host;

    # Rate limiting for auth
    limit_req zone=login burst=10 nodelay;
}
```

#### 5. Protected API Routes (`/aichatbot-api/*`)

```nginx
# AiChatBot Backend API (token auth required)
location /aichatbot-api/ {
    # Gateway token authentication
    auth_request /auth;
    error_page 401 = @auth_redirect;

    rewrite ^/aichatbot-api/(.*)$ /api/$1 break;
    proxy_pass http://127.0.0.1:8030;

    # Rate limiting
    limit_req zone=api burst=50 nodelay;
}
```

### Nginx Management

```bash
# Test configuration
nginx -t -c /Users/xuzhi/prod/gateway/config/nginx.conf

# Reload nginx (zero downtime)
nginx -s reload -c /Users/xuzhi/prod/gateway/config/nginx.conf

# View logs
tail -f /Users/xuzhi/prod/gateway/logs/access.log
tail -f /Users/xuzhi/prod/gateway/logs/error.log
```

---

## 📝 Deployment Process

### Automated Deployment (GitHub Actions)

**Trigger**: Push to main branch

```bash
git add .
git commit -m "your changes"
git push origin main
```

**Workflow automatically:**
1. SSH connects to Mac mini
2. Navigates to `~/AiChatBot`
3. Pulls latest code from GitHub
4. Exports secrets as environment variables
5. Runs `deployment/deploy-pm2.sh`
6. Verifies services are healthy
7. Reports success/failure

**Monitor deployment:**
```bash
# View workflow runs
gh run list

# Watch specific run
gh run watch

# View logs
gh run view --log
```

### Manual Deployment

On Mac mini:

```bash
# Navigate to source directory
cd ~/AiChatBot

# Pull latest code
git pull origin main

# Run deployment script
./deployment/deploy-pm2.sh
```

### What deploy-pm2.sh Does

1. **Backup**: Creates tarball of existing deployment
2. **Deploy Backend**:
   - Syncs backend files (excludes .venv, .env, .db)
   - Creates/updates `.env` from secrets
   - Sets up virtual environment
   - Installs Python dependencies
3. **Deploy Frontend**:
   - Builds production bundle with Vite
   - Syncs dist/ to production
4. **Update Nginx**:
   - Adds AiChatBot routes if not present
   - Tests configuration
   - Reloads nginx
5. **Manage PM2**:
   - Restarts existing processes or starts new ones
   - Saves PM2 configuration
6. **Verify**:
   - Checks backend health
   - Checks frontend serving
   - Displays PM2 status

---

## 🎮 Management Commands

### PM2 Commands

#### View Status

```bash
# List all processes
pm2 list

# Filter AiChatBot processes
pm2 list | grep aichatbot

# Detailed info
pm2 info aichatbot-backend
pm2 describe aichatbot-frontend
```

#### View Logs

```bash
# Live tail (all logs)
pm2 logs aichatbot

# Specific service
pm2 logs aichatbot-backend
pm2 logs aichatbot-frontend

# Last N lines
pm2 logs aichatbot-backend --lines 100

# Errors only
pm2 logs aichatbot-backend --err

# Output only
pm2 logs aichatbot-backend --out

# Stop tailing (Ctrl+C)
```

#### Restart Services

```bash
# Restart both
pm2 restart aichatbot-backend aichatbot-frontend

# Restart single service
pm2 restart aichatbot-backend

# Restart all PM2 apps
pm2 restart all

# Restart using ecosystem file (recommended)
cd /Users/xuzhi/prod/aichatbot
pm2 restart ecosystem.config.js
```

#### Stop/Start Services

```bash
# Stop
pm2 stop aichatbot-backend aichatbot-frontend

# Start
pm2 start aichatbot-backend aichatbot-frontend

# Start from ecosystem
cd /Users/xuzhi/prod/aichatbot
pm2 start ecosystem.config.js
```

#### Monitor Resources

```bash
# Real-time dashboard
pm2 monit

# CPU/Memory usage
pm2 describe aichatbot-backend

# Show metrics
pm2 show aichatbot-backend
```

#### Delete Processes

```bash
# Remove from PM2
pm2 delete aichatbot-backend aichatbot-frontend

# To re-add
cd /Users/xuzhi/prod/aichatbot
pm2 start ecosystem.config.js
pm2 save
```

### Quick Health Check Script

Create this helper script:

```bash
cat > ~/check-aichatbot.sh << 'EOF'
#!/bin/bash
echo "🔍 AiChatBot Health Check"
echo "========================"
echo ""

# Backend
echo "Backend (8030):"
curl -sf http://localhost:8030/health | python3 -m json.tool || echo "❌ Not responding"
echo ""

# Frontend
echo "Frontend (3030):"
HTTP_CODE=$(curl -sf -o /dev/null -w "%{http_code}" http://localhost:3030)
if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ HTTP $HTTP_CODE"
else
    echo "❌ HTTP $HTTP_CODE"
fi
echo ""

# Gateway
echo "Gateway (80):"
curl -sf http://localhost/health || echo "❌ Not responding"
echo ""

# PM2 Status
echo "PM2 Services:"
pm2 list | grep aichatbot || echo "❌ No processes found"
EOF

chmod +x ~/check-aichatbot.sh
```

Usage:
```bash
~/check-aichatbot.sh
```

---

## 🐛 Troubleshooting

### Problem: Frontend Shows Blank Page

**Symptoms**: Page loads but shows white/blank screen, title shows "frontend"

**Causes**:
1. Assets not loading (check browser console for 404 errors)
2. Vite build missing `base: '/aichatbot/'` configuration
3. Nginx not serving assets correctly

**Solution**:
```bash
# 1. Verify Vite config
cat ~/AiChatBot/frontend/vite.config.js
# Should have: base: '/aichatbot/',

# 2. Rebuild frontend
cd ~/AiChatBot/frontend
npm run build

# 3. Redeploy
cd ~/AiChatBot
./deployment/deploy-pm2.sh
```

---

### Problem: Registration Shows "Not Found"

**Symptoms**: Clicking register/login shows "Not Found" error

**Causes**:
1. API endpoint misconfigured in frontend
2. Backend not receiving requests
3. Nginx route not configured

**Solution**:
```bash
# 1. Test backend directly
curl -X POST http://localhost:8030/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test123"}'

# 2. Check nginx routes
grep -A 5 "location /aichatbot-api" /Users/xuzhi/prod/gateway/config/nginx.conf

# 3. Check frontend API URL
grep "getApiUrl" ~/AiChatBot/frontend/src/hooks/useAuth.js
# Should use: /aichatbot-api in production
```

---

### Problem: Stuck on "Connecting to chat..."

**Symptoms**: After login, stuck at "Connecting to chat..." message

**Causes**:
1. Socket.IO connection failing (CORS, authentication, or routing)
2. Backend not running
3. Port conflicts

**Solution**:
```bash
# 1. Check backend is running
curl http://localhost:8030/health
pm2 list | grep aichatbot-backend

# 2. Test Socket.IO endpoint
curl "http://localhost:8030/socket.io/?EIO=4&transport=polling"
# Should return: 0{"sid":"...","upgrades":["websocket"],...}

# 3. Check backend logs for connection errors
pm2 logs aichatbot-backend --lines 50 | grep -i "connect\|socket\|403"

# 4. Verify CORS settings in backend
grep "cors_allowed_origins" ~/AiChatBot/backend/main.py
# Should be: cors_allowed_origins="*"

# 5. Restart backend
pm2 restart aichatbot-backend
```

---

### Problem: 502 Bad Gateway

**Symptoms**: Nginx returns "502 Bad Gateway" error

**Causes**:
1. Backend not running on port 8030
2. Frontend not running on port 3030
3. Wrong ports in nginx config

**Solution**:
```bash
# 1. Check if services are running
pm2 list | grep aichatbot
lsof -i :8030
lsof -i :3030

# 2. Check nginx error logs
tail -50 /Users/xuzhi/prod/gateway/logs/error.log

# 3. Restart services
pm2 restart aichatbot-backend aichatbot-frontend

# 4. Wait for services to be ready
sleep 5
curl http://localhost:8030/health
curl http://localhost:3030
```

---

### Problem: Backend Not Starting (Port Already in Use)

**Symptoms**: PM2 shows "errored" status, logs show "address already in use"

**Causes**:
1. Old launchd services still running
2. Multiple PM2 processes
3. Stale Python processes

**Solution**:
```bash
# 1. Check what's using port 8030
lsof -i :8030

# 2. Stop launchd services
launchctl stop com.aichatbot.backend
launchctl unload ~/Library/LaunchAgents/com.aichatbot.backend.plist

# 3. Kill stale processes
kill $(lsof -ti :8030)

# 4. Restart PM2
pm2 restart aichatbot-backend
```

---

### Problem: GitHub Actions Deployment Fails

**Symptoms**: Workflow shows red X, logs show errors

**Common Issues:**

**SSH Connection Failed:**
```bash
# Test SSH from your machine
ssh -i ~/.ssh/aichatbot_deploy xuzhi@24.19.48.87

# Verify remote login enabled on Mac mini
sudo systemsetup -getremotelogin
# Should show: "Remote Login: On"

# Check SSH key permissions
chmod 600 ~/.ssh/aichatbot_deploy
```

**"npm: command not found":**
- PATH not set correctly in SSH session
- Fixed in workflow with explicit PATH export

**"sudo: a password is required":**
- `pm2 startup` requires sudo
- Now skipped in CI environment (CI=true flag)

**Secrets not working:**
- Verify secrets are set: `gh secret list --repo GeorgeZhiXu/AiChatBot`
- Check workflow uses `envs:` parameter
- Secrets are masked in logs as `***`

---

### Problem: Frontend on Random Ports

**Symptoms**: PM2 logs show "Accepting connections at http://localhost:54812"

**Cause**: `serve` command binding to random ports instead of 3030

**Solution**:
```bash
# Delete and recreate from ecosystem
pm2 delete aichatbot-frontend
cd /Users/xuzhi/prod/aichatbot
pm2 start ecosystem.config.js --only aichatbot-frontend
pm2 save

# Verify it's on 3030
lsof -i :3030
```

---

### Problem: Two Nginx Instances Running

**Symptoms**: Routes work locally but not externally, 404 errors from external IP

**Cause**: Default homebrew nginx running alongside gateway nginx

**Solution**:
```bash
# Stop homebrew nginx
brew services stop nginx

# Kill any stray nginx processes
killall nginx

# Verify only gateway nginx running
ps aux | grep nginx | grep gateway
```

---

## 📊 Monitoring & Maintenance

### Daily Health Checks

Run the health check script:
```bash
~/check-aichatbot.sh
```

Or manually:
```bash
# Services status
pm2 list | grep aichatbot

# Backend health
curl http://localhost:8030/health

# Frontend health
curl -I http://localhost:3030

# Gateway health
curl http://localhost/health

# View recent logs
pm2 logs aichatbot --lines 50
```

### Database Backups

#### Manual Backup

```bash
# Create backup
cp /Users/xuzhi/prod/aichatbot/backend/chat.db \
   /Users/xuzhi/prod/aichatbot/backups/chat-$(date +%Y%m%d-%H%M%S).db
```

#### Automated Daily Backup

Add to crontab:
```bash
crontab -e

# Add this line for daily 2 AM backup:
0 2 * * * cp /Users/xuzhi/prod/aichatbot/backend/chat.db /Users/xuzhi/prod/aichatbot/backups/chat-$(date +\%Y\%m\%d).db
```

#### Restore from Backup

```bash
# Stop backend
pm2 stop aichatbot-backend

# Restore database
cp /Users/xuzhi/prod/aichatbot/backups/chat-20251207.db \
   /Users/xuzhi/prod/aichatbot/backend/chat.db

# Restart backend
pm2 restart aichatbot-backend
```

### Deployment Backups

Automatic backups created before each deployment:
- **Location**: `/Users/xuzhi/prod/aichatbot/backups/`
- **Format**: `aichatbot-backup-YYYYMMDD-HHMMSS.tar.gz`
- **Contents**: Backend and frontend directories

#### Restore Deployment Backup

```bash
cd /Users/xuzhi/prod/aichatbot/backups

# List backups
ls -lh *.tar.gz

# Extract backup
tar -xzf aichatbot-backup-20251207-223000.tar.gz -C /Users/xuzhi/prod/aichatbot/

# Restart services
pm2 restart ecosystem.config.js
```

### Log Rotation

PM2 handles log rotation automatically. To manually clean old logs:

```bash
# Flush PM2 logs
pm2 flush

# Or manually archive
cd /Users/xuzhi/prod/aichatbot/logs
tar -czf logs-archive-$(date +%Y%m%d).tar.gz *.log
rm *.log
pm2 restart aichatbot-backend aichatbot-frontend
```

### Performance Monitoring

```bash
# Real-time resource monitoring
pm2 monit

# Check memory usage
pm2 describe aichatbot-backend | grep memory

# Check CPU usage
pm2 describe aichatbot-backend | grep cpu

# Check uptime
pm2 list | grep aichatbot
```

---

## 🔒 Security Considerations

### Secrets Management

**DO:**
- ✅ Store secrets in GitHub Secrets (encrypted)
- ✅ Keep `.env` in `.gitignore`
- ✅ Use strong random SECRET_KEY
- ✅ Rotate API keys regularly
- ✅ Use JWT tokens for authentication

**DON'T:**
- ❌ Commit secrets to git
- ❌ Share API keys
- ❌ Use weak passwords
- ❌ Disable authentication
- ❌ Expose internal ports externally

### Gateway Authentication

The nginx gateway provides two-layer security:

1. **Gateway Level**: Token-based auth for accessing `/aichatbot/`
2. **Application Level**: JWT auth for API requests

**Public Routes** (no gateway auth):
- `/health` - Health check
- `/auth-login` - Gateway login page
- `/aichatbot-api/auth/*` - Register/login endpoints
- `/aichatbot-api/socket.io/*` - WebSocket connections
- `/aichatbot/assets/*` - Static assets (CSS/JS)

**Protected Routes** (gateway auth required):
- `/` - Dashboard
- `/aichatbot/` - Chat interface
- `/aichatbot-api/rooms/*` - Room management
- All other API endpoints

### Rate Limiting

Configured in nginx:

```nginx
# General API: 10 req/s per IP, burst 50
limit_req zone=api burst=50 nodelay;

# Auth endpoints: 1 req/s per IP, burst 10
limit_req zone=login burst=10 nodelay;
```

### Firewall Recommendations

```bash
# Enable macOS firewall
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setglobalstate on

# Allow only necessary ports
# Port 80 (HTTP) - handled by firewall rules
# Port 22 (SSH) - for deployment
```

---

## 📚 Quick Reference

### File Locations

| Item | Path |
|------|------|
| Source Repository | `~/AiChatBot` |
| Production Root | `/Users/xuzhi/prod/aichatbot` |
| Backend Code | `/Users/xuzhi/prod/aichatbot/backend` |
| Frontend Build | `/Users/xuzhi/prod/aichatbot/frontend/dist` |
| Backend .env | `/Users/xuzhi/prod/aichatbot/backend/.env` |
| Database | `/Users/xuzhi/prod/aichatbot/backend/chat.db` |
| PM2 Config | `/Users/xuzhi/prod/aichatbot/ecosystem.config.js` |
| Backend Logs | `/Users/xuzhi/prod/aichatbot/logs/backend-*.log` |
| Frontend Logs | `/Users/xuzhi/prod/aichatbot/logs/frontend-*.log` |
| Backups | `/Users/xuzhi/prod/aichatbot/backups/` |
| Nginx Config | `/Users/xuzhi/prod/gateway/config/nginx.conf` |
| Nginx Logs | `/Users/xuzhi/prod/gateway/logs/` |

### Essential Commands

```bash
# Quick Status
pm2 list | grep aichatbot

# View Logs
pm2 logs aichatbot

# Restart Everything
pm2 restart aichatbot-backend aichatbot-frontend

# Deploy Latest Code
cd ~/AiChatBot && git pull && ./deployment/deploy-pm2.sh

# Check Health
curl http://localhost:8030/health
curl http://localhost:3030
curl http://localhost/health

# Test External Access
curl http://24.19.48.87/health
curl http://24.19.48.87/aichatbot/

# Reload Nginx
nginx -s reload -c /Users/xuzhi/prod/gateway/config/nginx.conf
```

### Access URLs

| Purpose | URL |
|---------|-----|
| Dashboard | http://24.19.48.87/ |
| AiChatBot | http://24.19.48.87/aichatbot/ |
| Backend API | http://24.19.48.87/aichatbot-api/ |
| Health Check | http://24.19.48.87/health |
| GitHub Repo | https://github.com/GeorgeZhiXu/AiChatBot |
| GitHub Actions | https://github.com/GeorgeZhiXu/AiChatBot/actions |
| GitHub Secrets | https://github.com/GeorgeZhiXu/AiChatBot/settings/secrets/actions |

---

## 🔄 Update & Rollback Procedures

### Update Application

#### Via GitHub (Recommended)

```bash
# From any machine
git add .
git commit -m "your changes"
git push origin main

# Automatically deploys via GitHub Actions
```

#### Manual Update

```bash
# On Mac mini
cd ~/AiChatBot
git pull origin main
./deployment/deploy-pm2.sh
```

### Rollback to Previous Version

#### Git Rollback

```bash
# On Mac mini
cd ~/AiChatBot

# View recent commits
git log --oneline -10

# Rollback to specific commit
git reset --hard <commit-hash>

# Redeploy
./deployment/deploy-pm2.sh
```

#### Restore from Backup

```bash
cd /Users/xuzhi/prod/aichatbot/backups

# List backups
ls -lht *.tar.gz | head -5

# Extract previous backup
tar -xzf aichatbot-backup-20251207-220000.tar.gz -C /Users/xuzhi/prod/aichatbot/

# Restart services
pm2 restart ecosystem.config.js
```

---

## 💡 Best Practices

### Development Workflow

1. **Develop locally** with hot reload
   ```bash
   cd ~/AiChatBot/backend
   source .venv/bin/activate
   uvicorn main:asgi_app --reload

   cd ~/AiChatBot/frontend
   npm run dev
   ```

2. **Test locally** before committing

3. **Commit and push** to trigger deployment
   ```bash
   git add .
   git commit -m "descriptive message"
   git push origin main
   ```

4. **Monitor deployment** in GitHub Actions

5. **Verify production** after deployment
   ```bash
   ~/check-aichatbot.sh
   ```

### Deployment Best Practices

- ✅ Always test locally before pushing
- ✅ Write descriptive commit messages
- ✅ Check GitHub Actions logs after deployment
- ✅ Monitor PM2 logs after deployment
- ✅ Keep backups of database
- ✅ Update secrets when they change
- ✅ Review nginx logs for errors

### Maintenance Schedule

**Daily:**
- Monitor PM2 process status
- Check error logs for issues

**Weekly:**
- Review disk usage
- Clean old log files
- Check for security updates

**Monthly:**
- Rotate API keys if needed
- Review and clean old backups
- Update dependencies

---

## 📖 Additional Resources

### Documentation Files

- **DEPLOYMENT_PM2.md** - Detailed PM2 deployment guide
- **GITHUB_SECRETS.md** - GitHub Secrets setup instructions
- **DEPLOYMENT.md** - Legacy launchd deployment (deprecated)
- **README.md** - Project overview and features

### External Links

- **PM2 Documentation**: https://pm2.keymetrics.io/docs/usage/quick-start/
- **Nginx Documentation**: http://nginx.org/en/docs/
- **GitHub Actions**: https://docs.github.com/en/actions
- **DeepSeek Platform**: https://platform.deepseek.com/
- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **Socket.IO Docs**: https://socket.io/docs/v4/

---

## 🎯 Success Checklist

After deployment, verify all items:

- [ ] GitHub Secrets configured (5 secrets)
- [ ] PM2 processes online: `pm2 list | grep aichatbot`
- [ ] Backend healthy: `curl http://localhost:8030/health`
- [ ] Frontend serving: `curl http://localhost:3030`
- [ ] Gateway responding: `curl http://24.19.48.87/health`
- [ ] Can access dashboard: http://24.19.48.87/
- [ ] Can login to gateway
- [ ] Can access AiChatBot: http://24.19.48.87/aichatbot/
- [ ] Can register new user
- [ ] Chat connects successfully (no stuck "Connecting...")
- [ ] Can send messages
- [ ] `@AI` triggers AI responses
- [ ] PM2 startup configured for auto-boot
- [ ] Backups directory exists
- [ ] Logs are rotating properly

---

## 🆘 Getting Help

### Check Logs First

```bash
# PM2 logs
pm2 logs aichatbot --lines 100

# Nginx logs
tail -100 /Users/xuzhi/prod/gateway/logs/error.log
tail -100 /Users/xuzhi/prod/gateway/logs/access.log

# GitHub Actions logs
gh run view --log
```

### Common Commands for Support

```bash
# System info
uname -a
sw_vers

# Service status
pm2 list
ps aux | grep nginx
lsof -i :80 -i :3030 -i :8030

# Network test
curl -v http://localhost:8030/health
curl -v http://24.19.48.87/aichatbot/

# Environment check
which pm2
which node
which python3
node --version
python3 --version
pm2 --version
```

---

## 🎉 Deployment Complete!

Your AiChatBot is now fully deployed with:
- ✅ Automated CI/CD via GitHub Actions
- ✅ PM2 process management
- ✅ Nginx gateway integration
- ✅ Zero-downtime deployments
- ✅ Automatic backups
- ✅ Health monitoring
- ✅ Log management
- ✅ WebSocket support

**Access your application**: http://24.19.48.87/aichatbot/

Happy chatting with AI! 🤖💬
