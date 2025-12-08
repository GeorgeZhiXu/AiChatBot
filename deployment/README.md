# 📁 Deployment Directory

This directory contains all deployment-related scripts and configurations for AiChatBot.

---

## 📄 Files in This Directory

### Active Files (PM2 Deployment)

| File | Purpose | Usage |
|------|---------|-------|
| `deploy-pm2.sh` | Main deployment script for PM2 | `./deployment/deploy-pm2.sh` |

This script:
- Creates production directory structure
- Deploys backend and frontend
- Configures nginx gateway routes
- Manages PM2 processes
- Verifies deployment health

### Legacy Files (Deprecated - LaunchD)

These files are from the old launchd-based deployment and are **no longer used**:

| File | Purpose | Status |
|------|---------|--------|
| `setup.sh` | Old setup script | ⚠️ Deprecated |
| `remote-setup.sh` | Old remote setup | ⚠️ Deprecated |
| `backend-start.sh` | LaunchD backend script | ⚠️ Deprecated |
| `frontend-start.sh` | LaunchD frontend script | ⚠️ Deprecated |
| `com.aichatbot.backend.plist` | LaunchD config | ⚠️ Deprecated |
| `com.aichatbot.frontend.plist` | LaunchD config | ⚠️ Deprecated |
| `nginx-aichatbot.conf` | Old nginx config | ⚠️ Deprecated |
| `QUICKSTART.md` | Old quick start guide | ⚠️ Deprecated |

**Note**: These files are kept for reference but should not be used. The new PM2-based deployment replaces all of these.

---

## 🚀 Deployment Methods

### Method 1: Automated (Recommended)

**Via GitHub Actions** - Just push your code:

```bash
git add .
git commit -m "your changes"
git push origin main
```

GitHub Actions automatically deploys to your Mac mini.

### Method 2: Manual Deployment

**On Mac mini** - Run deployment script:

```bash
cd ~/AiChatBot
git pull origin main
./deployment/deploy-pm2.sh
```

---

## 📖 Documentation

All deployment documentation is in the repository root:

### Main Guides

- **[../DEPLOYMENT_GUIDE.md](../DEPLOYMENT_GUIDE.md)** - Complete deployment guide
  - Architecture overview
  - Initial setup steps
  - Configuration details
  - Troubleshooting guide

- **[../GITHUB_ACTIONS.md](../GITHUB_ACTIONS.md)** - CI/CD workflow guide
  - GitHub Actions setup
  - Secrets configuration
  - Monitoring deployments
  - Debugging workflows

- **[../DEPLOYMENT_PM2.md](../DEPLOYMENT_PM2.md)** - PM2 management guide
  - PM2 configuration
  - Process management
  - Log management
  - Monitoring commands

### Quick References

- **[../QUICK_REFERENCE.md](../QUICK_REFERENCE.md)** - One-page command reference
- **[../GITHUB_SECRETS.md](../GITHUB_SECRETS.md)** - Secrets setup guide
- **[../SETUP_COMPLETE.md](../SETUP_COMPLETE.md)** - Deployment completion summary

---

## 🔧 Script Details

### deploy-pm2.sh

**Location**: `deployment/deploy-pm2.sh`

**What it does:**

1. **Setup**: Creates directory structure, checks prerequisites
2. **Backup**: Archives existing deployment
3. **Backend Deployment**:
   - Syncs backend files
   - Creates/updates .env from environment variables
   - Sets up Python virtual environment
   - Installs dependencies
4. **Frontend Deployment**:
   - Builds production bundle with Vite
   - Syncs dist/ directory to production
5. **Nginx Configuration**:
   - Adds AiChatBot routes if not present
   - Tests configuration
   - Reloads nginx
6. **PM2 Management**:
   - Starts or restarts processes
   - Saves configuration
7. **Verification**:
   - Tests backend health
   - Tests frontend serving
   - Displays status

**Requirements:**
- Must run on Mac mini
- Requires npm, python3, pm2 installed
- Requires write access to `/Users/xuzhi/prod/`

**Usage:**

```bash
# Standard deployment
./deployment/deploy-pm2.sh

# With GitHub Secrets (in CI)
export DEEPSEEK_API_KEY="sk-xxx"
export SECRET_KEY="xxx"
./deployment/deploy-pm2.sh
```

---

## 🗂️ Directory Structure After Deployment

```
/Users/xuzhi/prod/aichatbot/
├── backend/
│   ├── .venv/                    # Python virtual environment
│   ├── .env                      # Secrets (auto-generated)
│   ├── main.py                   # FastAPI app
│   ├── chat.db                   # SQLite database
│   └── ... (other backend files)
│
├── frontend/
│   └── dist/                     # Built React app
│       ├── index.html
│       ├── assets/
│       │   ├── index-xxx.js
│       │   └── index-xxx.css
│       └── vite.svg
│
├── logs/
│   ├── backend-error.log
│   ├── backend-out.log
│   ├── frontend-error.log
│   └── frontend-out.log
│
├── backups/
│   ├── aichatbot-backup-20251208-120000.tar.gz
│   └── chat-20251208.db
│
└── ecosystem.config.js           # PM2 configuration
```

---

## 🔄 Migration from LaunchD

If you had the old launchd-based deployment:

### 1. Stop Old Services

```bash
# Stop launchd services
launchctl stop com.aichatbot.backend
launchctl stop com.aichatbot.frontend

# Unload plists
launchctl unload ~/Library/LaunchAgents/com.aichatbot.backend.plist
launchctl unload ~/Library/LaunchAgents/com.aichatbot.frontend.plist

# Remove plist files (optional)
rm ~/Library/LaunchAgents/com.aichatbot.*
```

### 2. Run New PM2 Deployment

```bash
cd ~/AiChatBot
./deployment/deploy-pm2.sh
```

### 3. Verify PM2 Services

```bash
pm2 list | grep aichatbot
pm2 logs aichatbot
```

---

## 📞 Support

### Quick Help Commands

```bash
# Service status
pm2 list

# View logs
pm2 logs aichatbot

# Health check
~/check-aichatbot.sh

# Restart everything
pm2 restart aichatbot-backend aichatbot-frontend
```

### Getting More Help

- **Documentation**: See main guides in repository root
- **GitHub Actions**: Check workflow runs for deployment issues
- **Logs**: `pm2 logs` and nginx logs in `/Users/xuzhi/prod/gateway/logs/`

---

## ✅ Deployment Checklist

Before considering deployment complete:

- [x] PM2 processes online
- [x] Backend responding on 8030
- [x] Frontend serving on 3030
- [x] Nginx routes configured
- [x] Gateway accessible externally
- [x] GitHub Actions workflow active
- [x] All secrets configured
- [x] Can register/login users
- [x] Chat connects successfully
- [x] AI responses work
- [x] Documentation complete

---

**All deployment files are ready to use!** 🎉

For complete setup instructions, see: [../DEPLOYMENT_GUIDE.md](../DEPLOYMENT_GUIDE.md)
