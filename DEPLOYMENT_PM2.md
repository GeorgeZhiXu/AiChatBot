# 🚀 AiChatBot PM2 + Gateway Deployment Guide

This guide covers deploying AiChatBot to your Mac mini using PM2 for process management and integrating with the existing nginx gateway.

## 📋 Overview

### Deployment Architecture

```
Internet/LAN → nginx Gateway (:80) → AiChatBot
                      ↓
               /aichatbot/ → Frontend (:3030) - React App
               /aichatbot-api/ → Backend (:8030) - FastAPI + Socket.IO
```

### Directory Structure

```
/Users/xuzhi/prod/aichatbot/
├── backend/                # Backend FastAPI application
│   ├── .venv/             # Python virtual environment
│   ├── .env               # Environment variables (API keys)
│   ├── main.py
│   └── ...
├── frontend/              # Frontend React application
│   └── dist/              # Production build
├── logs/                  # Application logs
│   ├── backend-error.log
│   ├── backend-out.log
│   ├── frontend-error.log
│   └── frontend-out.log
├── backups/               # Deployment backups
└── ecosystem.config.js    # PM2 configuration
```

### Port Configuration

- **Frontend**: 3030 (served via `npx serve`)
- **Backend**: 8030 (uvicorn)
- **Gateway**: 80 (nginx reverse proxy)

---

## 🛠️ Prerequisites

### On Mac mini

1. **nginx gateway** (already configured at `/Users/xuzhi/prod/gateway`)
2. **Node.js 16+** with npm
3. **Python 3.12+**
4. **PM2** (process manager)

```bash
# Install PM2 globally if not already installed
npm install -g pm2

# Install serve globally (for frontend static hosting)
npm install -g serve
```

---

## 🚀 Initial Setup (One-time)

### 1. Clone Repository to Mac mini

```bash
cd ~
git clone https://github.com/GeorgeZhiXu/AiChatBot.git
cd AiChatBot
```

### 2. Run Initial Deployment

```bash
# Make deployment script executable
chmod +x deployment/deploy-pm2.sh

# Run deployment (will create directory structure, setup services, update nginx)
./deployment/deploy-pm2.sh
```

**The script will:**
- ✅ Create `/Users/xuzhi/prod/aichatbot/` directory structure
- ✅ Copy application files
- ✅ Setup Python virtual environment and install dependencies
- ✅ Build frontend production bundle
- ✅ Configure PM2 ecosystem
- ✅ Add AiChatBot routes to nginx gateway
- ✅ Start PM2 processes
- ✅ Setup PM2 to start on system boot

### 3. Configure Environment Variables

Edit the `.env` file with your API keys:

```bash
nano /Users/xuzhi/prod/aichatbot/backend/.env
```

Required variables:
```env
DEEPSEEK_API_KEY=your-api-key-here
DEEPSEEK_API_BASE=https://api.deepseek.com
SECRET_KEY=your-jwt-secret-here
DATABASE_URL=sqlite:///./chat.db
```

After editing, restart the backend:
```bash
pm2 restart aichatbot-backend
```

---

## 🔄 Automated Deployment (GitHub Actions)

### Setup GitHub Secrets

Go to your repository settings and add these secrets:
`https://github.com/GeorgeZhiXu/AiChatBot/settings/secrets/actions`

**Required Secrets:**
- `MAC_MINI_HOST`: IP address or hostname (e.g., `24.19.51.52` or `xuzhi.ddns.net`)
- `MAC_MINI_USER`: Your Mac mini username (e.g., `xuzhi`)
- `MAC_MINI_SSH_KEY`: Your SSH private key
- `MAC_MINI_SSH_PORT`: SSH port (default: `22`)

### Generate SSH Key (if needed)

```bash
# On your Mac mini
ssh-keygen -t ed25519 -C "github-actions-aichatbot" -f ~/.ssh/aichatbot_deploy

# Add public key to authorized_keys
cat ~/.ssh/aichatbot_deploy.pub >> ~/.ssh/authorized_keys

# Copy private key content for GitHub secret
cat ~/.ssh/aichatbot_deploy
```

### Deploy via Git Push

Once secrets are configured, deployments happen automatically:

```bash
# Make changes to your code
git add .
git commit -m "Update feature"
git push origin main
```

GitHub Actions will:
1. SSH into your Mac mini
2. Pull latest code
3. Run `deploy-pm2.sh` script
4. Verify deployment health
5. Show deployment summary

### Manual Trigger

You can also trigger deployment manually from GitHub Actions UI:
`https://github.com/GeorgeZhiXu/AiChatBot/actions`

---

## 🔧 PM2 Management Commands

### View Process Status

```bash
# List all processes
pm2 list

# Filter AiChatBot processes
pm2 list | grep aichatbot
```

### View Logs

```bash
# View all AiChatBot logs (live stream)
pm2 logs aichatbot

# View specific process
pm2 logs aichatbot-backend
pm2 logs aichatbot-frontend

# View last 100 lines
pm2 logs aichatbot-backend --lines 100

# View errors only
pm2 logs aichatbot-backend --err
```

### Restart Services

```bash
# Restart both services
pm2 restart aichatbot-backend aichatbot-frontend

# Restart backend only
pm2 restart aichatbot-backend

# Restart frontend only
pm2 restart aichatbot-frontend

# Restart using ecosystem file (recommended)
cd /Users/xuzhi/prod/aichatbot
pm2 restart ecosystem.config.js
```

### Stop/Start Services

```bash
# Stop services
pm2 stop aichatbot-backend aichatbot-frontend

# Start services
pm2 start aichatbot-backend aichatbot-frontend

# Start using ecosystem file
cd /Users/xuzhi/prod/aichatbot
pm2 start ecosystem.config.js
```

### Delete Processes

```bash
# Delete (remove from PM2)
pm2 delete aichatbot-backend aichatbot-frontend

# To re-add, use ecosystem file
cd /Users/xuzhi/prod/aichatbot
pm2 start ecosystem.config.js
```

### Monitor Resources

```bash
# Real-time monitoring dashboard
pm2 monit

# Process information
pm2 info aichatbot-backend

# Show process metrics
pm2 describe aichatbot-backend
```

### Save PM2 Configuration

```bash
# Save current process list (persists across reboots)
pm2 save

# Setup PM2 to start on boot
pm2 startup launchd
```

---

## 🌐 Access URLs

### Direct Access (without gateway)
- **Frontend**: http://localhost:3030
- **Backend**: http://localhost:8030
- **Health Check**: http://localhost:8030/health

### Via Gateway (with authentication)
- **Application**: http://your-mac-mini-ip/aichatbot/
- **Backend API**: http://your-mac-mini-ip/aichatbot-api/
- **Health Check**: http://your-mac-mini-ip/health

### Examples
```bash
# Local testing
curl http://localhost:8030/health
curl http://localhost:3030

# Gateway access
curl http://24.19.51.52/health
curl http://xuzhi.ddns.net/aichatbot/
```

---

## 🔐 Gateway Integration

The deployment script automatically adds these nginx routes to your gateway:

### Frontend Route (`/aichatbot/`)
- Serves the React frontend
- Requires token authentication
- Supports WebSocket for Socket.IO
- Proxies to `http://127.0.0.1:3030`

### Backend Route (`/aichatbot-api/`)
- Proxies backend API requests
- Requires token authentication
- Supports WebSocket for Socket.IO
- Proxies to `http://127.0.0.1:8030`
- Has rate limiting (50 requests burst)

### Nginx Configuration Location
- Config file: `/Users/xuzhi/prod/gateway/config/nginx.conf`
- Logs: `/Users/xuzhi/prod/gateway/logs/`

### Reload Nginx After Changes

```bash
# Test configuration
nginx -t -c /Users/xuzhi/prod/gateway/config/nginx.conf

# Reload nginx
nginx -s reload -c /Users/xuzhi/prod/gateway/config/nginx.conf
```

---

## 📊 Monitoring & Maintenance

### Check Service Health

```bash
# Quick health check script
cat > ~/check-aichatbot.sh << 'EOF'
#!/bin/bash
echo "🔍 AiChatBot Health Check"
echo "========================"
echo ""
echo "Backend (8030):"
curl -s http://localhost:8030/health | python3 -m json.tool || echo "❌ Not responding"
echo ""
echo "Frontend (3030):"
curl -s -o /dev/null -w "HTTP Status: %{http_code}" http://localhost:3030
echo ""
echo ""
echo "PM2 Status:"
pm2 list | grep aichatbot
EOF

chmod +x ~/check-aichatbot.sh
./check-aichatbot.sh
```

### Log Rotation

PM2 automatically manages log rotation. Configure in ecosystem file:

```javascript
// ecosystem.config.js
{
  max_memory_restart: '500M',  // Restart if memory exceeds 500MB
  error_file: '/path/to/error.log',
  out_file: '/path/to/out.log',
  log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
  merge_logs: true
}
```

### Database Backup

```bash
# Manual backup
cp /Users/xuzhi/prod/aichatbot/backend/chat.db \
   /Users/xuzhi/prod/aichatbot/backups/chat-$(date +%Y%m%d-%H%M%S).db

# Automated daily backup (add to crontab)
crontab -e

# Add this line for daily 2 AM backup:
# 0 2 * * * cp /Users/xuzhi/prod/aichatbot/backend/chat.db /Users/xuzhi/prod/aichatbot/backups/chat-$(date +\%Y\%m\%d).db
```

### Deployment Backups

The deployment script automatically creates backups before each deployment:
- Location: `/Users/xuzhi/prod/aichatbot/backups/`
- Format: `aichatbot-backup-YYYYMMDD-HHMMSS.tar.gz`

To restore a backup:
```bash
cd /Users/xuzhi/prod/aichatbot/backups
tar -xzf aichatbot-backup-20251207-120000.tar.gz -C /Users/xuzhi/prod/aichatbot/
pm2 restart ecosystem.config.js
```

---

## 🐛 Troubleshooting

### Problem: Backend Not Starting

```bash
# Check backend logs
pm2 logs aichatbot-backend --lines 50

# Check if port is already in use
lsof -i :8030

# Verify .env file exists
cat /Users/xuzhi/prod/aichatbot/backend/.env

# Test manual start
cd /Users/xuzhi/prod/aichatbot/backend
source .venv/bin/activate
uvicorn main:asgi_app --host 0.0.0.0 --port 8030
```

### Problem: Frontend Not Serving

```bash
# Check frontend logs
pm2 logs aichatbot-frontend --lines 50

# Verify dist directory exists
ls -la /Users/xuzhi/prod/aichatbot/frontend/dist/

# Rebuild frontend
cd ~/AiChatBot/frontend
npm install
npm run build
rsync -av dist/ /Users/xuzhi/prod/aichatbot/frontend/dist/
pm2 restart aichatbot-frontend
```

### Problem: PM2 Process Not Starting on Boot

```bash
# Re-setup PM2 startup
pm2 unstartup launchd
pm2 startup launchd -u $(whoami) --hp $HOME

# Save current process list
pm2 save

# Test by rebooting
sudo reboot
```

### Problem: Gateway Returns 502 Bad Gateway

```bash
# Check if backend is running
curl http://localhost:8030/health

# Check nginx error logs
tail -f /Users/xuzhi/prod/gateway/logs/error.log

# Test nginx configuration
nginx -t -c /Users/xuzhi/prod/gateway/config/nginx.conf

# Restart nginx
nginx -s reload -c /Users/xuzhi/prod/gateway/config/nginx.conf
```

### Problem: Socket.IO Not Connecting

```bash
# Verify WebSocket upgrade headers in nginx config
grep -A 5 "location /aichatbot/" /Users/xuzhi/prod/gateway/config/nginx.conf

# Should include:
# proxy_http_version 1.1;
# proxy_set_header Upgrade $http_upgrade;
# proxy_set_header Connection "upgrade";

# Check backend Socket.IO endpoint
curl -i http://localhost:8030/socket.io/
```

### Problem: GitHub Actions Deployment Fails

```bash
# Verify SSH access from GitHub
ssh -i ~/.ssh/aichatbot_deploy xuzhi@24.19.51.52

# Check SSH key permissions
chmod 600 ~/.ssh/aichatbot_deploy
chmod 644 ~/.ssh/aichatbot_deploy.pub

# Verify remote login is enabled
sudo systemsetup -getremotelogin

# Check GitHub secrets are set correctly
# Go to: https://github.com/GeorgeZhiXu/AiChatBot/settings/secrets/actions
```

---

## 🔄 Manual Deployment

If you need to deploy without GitHub Actions:

```bash
# On Mac mini
cd ~/AiChatBot

# Pull latest code
git pull origin main

# Run deployment
./deployment/deploy-pm2.sh
```

---

## 📚 Additional Resources

### Useful Commands Reference

```bash
# PM2
pm2 list                           # List processes
pm2 logs aichatbot                 # View logs
pm2 restart aichatbot-backend      # Restart backend
pm2 monit                          # Monitor dashboard
pm2 save                           # Save process list

# Nginx
nginx -t -c /Users/xuzhi/prod/gateway/config/nginx.conf    # Test config
nginx -s reload -c /Users/xuzhi/prod/gateway/config/nginx.conf  # Reload

# Service health checks
curl http://localhost:8030/health  # Backend health
curl http://localhost:3030         # Frontend health
pm2 list | grep aichatbot          # PM2 process status
```

### File Locations

| Item | Location |
|------|----------|
| Production directory | `/Users/xuzhi/prod/aichatbot/` |
| Backend .env | `/Users/xuzhi/prod/aichatbot/backend/.env` |
| PM2 ecosystem | `/Users/xuzhi/prod/aichatbot/ecosystem.config.js` |
| Backend logs | `/Users/xuzhi/prod/aichatbot/logs/backend-*.log` |
| Frontend logs | `/Users/xuzhi/prod/aichatbot/logs/frontend-*.log` |
| Database | `/Users/xuzhi/prod/aichatbot/backend/chat.db` |
| Gateway config | `/Users/xuzhi/prod/gateway/config/nginx.conf` |
| Gateway logs | `/Users/xuzhi/prod/gateway/logs/` |
| Backups | `/Users/xuzhi/prod/aichatbot/backups/` |

---

## 🎉 Success Checklist

After deployment, verify:

- [ ] PM2 processes running: `pm2 list | grep aichatbot`
- [ ] Backend health: `curl http://localhost:8030/health`
- [ ] Frontend serving: `curl http://localhost:3030`
- [ ] Gateway access: Visit `http://your-ip/aichatbot/`
- [ ] WebSocket working: Test chat functionality
- [ ] Logs accessible: `pm2 logs aichatbot`
- [ ] Auto-restart on boot: `pm2 startup` configured
- [ ] Environment variables set: Check `.env` file

---

## 📞 Support

If you encounter issues:

1. Check logs: `pm2 logs aichatbot`
2. Review troubleshooting section above
3. Check GitHub Actions logs for deployment issues
4. Verify all prerequisites are installed

---

**Happy Deploying! 🚀**
