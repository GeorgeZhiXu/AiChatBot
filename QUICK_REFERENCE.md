# ⚡ AiChatBot Quick Reference Card

Essential commands and information for daily operations.

---

## 🌐 Access URLs

```
Dashboard:    http://24.19.48.87/
AiChatBot:    http://24.19.48.87/aichatbot/
Backend API:  http://24.19.48.87/aichatbot-api/
Health:       http://24.19.48.87/health

Frontend:     http://localhost:3030
Backend:      http://localhost:8030
```

---

## 🎮 PM2 Commands

### Status & Monitoring
```bash
pm2 list                          # List all processes
pm2 list | grep aichatbot         # Filter AiChatBot
pm2 info aichatbot-backend        # Detailed info
pm2 monit                         # Real-time dashboard
```

### Logs
```bash
pm2 logs aichatbot                # Live tail (both services)
pm2 logs aichatbot-backend        # Backend only
pm2 logs aichatbot-frontend       # Frontend only
pm2 logs aichatbot --lines 100    # Last 100 lines
pm2 logs aichatbot --err          # Errors only
pm2 flush                         # Clear all logs
```

### Restart/Stop/Start
```bash
pm2 restart aichatbot-backend aichatbot-frontend
pm2 restart all
pm2 stop aichatbot-backend
pm2 start aichatbot-backend
pm2 delete aichatbot-backend      # Remove from PM2
pm2 save                          # Save process list
```

---

## 🌐 Nginx Commands

```bash
# Test configuration
nginx -t -c /Users/xuzhi/prod/gateway/config/nginx.conf

# Reload (zero downtime)
nginx -s reload -c /Users/xuzhi/prod/gateway/config/nginx.conf

# View logs
tail -f /Users/xuzhi/prod/gateway/logs/access.log
tail -f /Users/xuzhi/prod/gateway/logs/error.log

# Check processes
ps aux | grep nginx | grep gateway
```

---

## 🔄 Deployment

### Automatic (GitHub Actions)
```bash
git add .
git commit -m "your changes"
git push origin main
# Auto-deploys via GitHub Actions
```

### Manual
```bash
cd ~/AiChatBot
git pull origin main
./deployment/deploy-pm2.sh
```

### Monitor Deployment
```bash
gh run list                       # List recent runs
gh run watch                      # Watch current run
gh run view <id> --log           # View logs
```

---

## 🔍 Health Checks

```bash
# Quick check all services
~/check-aichatbot.sh

# Individual checks
curl http://localhost:8030/health
curl http://localhost:3030
curl http://localhost/health
pm2 list | grep aichatbot
```

---

## 🐛 Quick Fixes

### Backend Not Responding
```bash
pm2 restart aichatbot-backend
pm2 logs aichatbot-backend --lines 50
```

### Frontend Not Loading
```bash
pm2 restart aichatbot-frontend
curl -I http://localhost:3030
```

### Port Conflicts
```bash
lsof -i :8030                     # Check port 8030
lsof -i :3030                     # Check port 3030
kill <PID>                        # Kill process
pm2 restart aichatbot-backend
```

### Stuck "Connecting to chat..."
```bash
pm2 restart aichatbot-backend     # Restart backend
curl "http://localhost:8030/socket.io/?EIO=4&transport=polling"
```

### 502 Bad Gateway
```bash
pm2 list | grep aichatbot         # Check services running
pm2 restart aichatbot-backend aichatbot-frontend
nginx -s reload -c /Users/xuzhi/prod/gateway/config/nginx.conf
```

---

## 📂 Important Paths

```
Source:         ~/AiChatBot
Production:     /Users/xuzhi/prod/aichatbot
Backend:        /Users/xuzhi/prod/aichatbot/backend
Frontend:       /Users/xuzhi/prod/aichatbot/frontend/dist
.env file:      /Users/xuzhi/prod/aichatbot/backend/.env
Database:       /Users/xuzhi/prod/aichatbot/backend/chat.db
Logs:           /Users/xuzhi/prod/aichatbot/logs/
Backups:        /Users/xuzhi/prod/aichatbot/backups/
Nginx config:   /Users/xuzhi/prod/gateway/config/nginx.conf
Nginx logs:     /Users/xuzhi/prod/gateway/logs/
```

---

## 🔐 GitHub Secrets

Required secrets (https://github.com/GeorgeZhiXu/AiChatBot/settings/secrets/actions):

```
MAC_MINI_HOST       # 24.19.48.87
MAC_MINI_USER       # xuzhi
MAC_MINI_SSH_KEY    # SSH private key
MAC_MINI_SSH_PORT   # 22 (optional)
DEEPSEEK_API_KEY    # sk-xxx...
SECRET_KEY          # JWT secret (32 hex chars)
```

### Update Secret
```bash
gh secret set DEEPSEEK_API_KEY --body "new-key"
gh secret list                    # Verify
```

---

## 💾 Backup & Restore

### Database Backup
```bash
# Manual backup
cp /Users/xuzhi/prod/aichatbot/backend/chat.db \
   /Users/xuzhi/prod/aichatbot/backups/chat-$(date +%Y%m%d).db

# Restore
pm2 stop aichatbot-backend
cp /Users/xuzhi/prod/aichatbot/backups/chat-20251207.db \
   /Users/xuzhi/prod/aichatbot/backend/chat.db
pm2 restart aichatbot-backend
```

### Full Deployment Backup
```bash
# Backups created automatically before each deployment
ls -lh /Users/xuzhi/prod/aichatbot/backups/

# Restore
cd /Users/xuzhi/prod/aichatbot/backups
tar -xzf aichatbot-backup-20251207-120000.tar.gz \
  -C /Users/xuzhi/prod/aichatbot/
pm2 restart ecosystem.config.js
```

---

## 🔧 Configuration Files

### PM2 Ecosystem
```
/Users/xuzhi/prod/aichatbot/ecosystem.config.js
```

### Environment Variables
```
/Users/xuzhi/prod/aichatbot/backend/.env
```

### Nginx Routes
```
/Users/xuzhi/prod/gateway/config/nginx.conf

Routes:
  /aichatbot/              → Frontend (:3030)
  /aichatbot/assets/       → Static assets (no auth)
  /aichatbot-api/auth/     → Auth endpoints (no auth)
  /aichatbot-api/socket.io/ → WebSocket (no auth)
  /aichatbot-api/*         → Protected API (auth required)
```

---

## 📊 Port Mapping

| Service | Port | Access | Protocol |
|---------|------|--------|----------|
| Nginx Gateway | 80 | External | HTTP |
| Frontend (serve) | 3030 | Internal | HTTP |
| Backend (uvicorn) | 8030 | Internal | HTTP/WS |

---

## 🎯 Common Tasks

### Deploy Latest Code
```bash
git push origin main              # Auto-deploy
# OR
cd ~/AiChatBot && git pull && ./deployment/deploy-pm2.sh
```

### View Live Logs
```bash
pm2 logs aichatbot                # All services
# Press Ctrl+C to stop tailing
```

### Check Service Health
```bash
~/check-aichatbot.sh
# OR
curl http://localhost:8030/health && \
curl http://localhost:3030 && \
pm2 list | grep aichatbot
```

### Restart After Config Change
```bash
# After editing .env
pm2 restart aichatbot-backend

# After nginx config change
nginx -t -c /Users/xuzhi/prod/gateway/config/nginx.conf
nginx -s reload -c /Users/xuzhi/prod/gateway/config/nginx.conf
```

### Full Service Restart
```bash
pm2 restart aichatbot-backend aichatbot-frontend
pm2 save
```

---

## 📞 Support & Documentation

**Full Documentation:**
- `DEPLOYMENT_GUIDE.md` - Complete deployment guide
- `GITHUB_ACTIONS.md` - CI/CD workflow details
- `DEPLOYMENT_PM2.md` - PM2 management guide
- `GITHUB_SECRETS.md` - Secrets configuration

**GitHub:**
- Actions: https://github.com/GeorgeZhiXu/AiChatBot/actions
- Secrets: https://github.com/GeorgeZhiXu/AiChatBot/settings/secrets/actions
- Issues: https://github.com/GeorgeZhiXu/AiChatBot/issues

**Quick Help:**
```bash
pm2 --help                        # PM2 help
nginx -h                          # Nginx help
gh help                           # GitHub CLI help
```

---

**Print this page for quick reference!** 📄
