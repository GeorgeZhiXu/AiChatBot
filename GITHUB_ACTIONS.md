# 🔄 GitHub Actions CI/CD Guide

Complete guide for understanding and managing the automated deployment workflow.

---

## 📋 Overview

The GitHub Actions workflow provides fully automated deployments to your Mac mini whenever code is pushed to the main branch.

**Workflow File**: `.github/workflows/deploy-pm2.yml`

### What It Does

1. ✅ Automatically triggers on push to `main`
2. ✅ SSH connects to your Mac mini
3. ✅ Pulls latest code
4. ✅ Configures environment with GitHub Secrets
5. ✅ Builds and deploys application
6. ✅ Restarts services with PM2
7. ✅ Verifies deployment health
8. ✅ Reports success/failure

---

## 🔧 Workflow Configuration

### Trigger Events

```yaml
on:
  push:
    branches:
      - main
    paths-ignore:
      - 'README.md'
      - 'docs/**'
      - '**.md'
  workflow_dispatch:
```

**Triggers:**
- **Automatic**: Any push to `main` branch (except .md files)
- **Manual**: Click "Run workflow" in GitHub Actions UI

### Workflow Steps Explained

#### 1. Checkout Code
```yaml
- name: Checkout code
  uses: actions/checkout@v4
```
Checks out your repository code in the GitHub runner.

#### 2. Deploy via SSH
```yaml
- name: Deploy to Mac Mini via SSH
  uses: appleboy/ssh-action@v1.0.0
```

Uses the SSH action to:
- Connect to Mac mini using secrets
- Execute deployment script remotely
- Stream output back to GitHub

**Environment Variables Passed:**
- `CI=true` - Indicates CI environment
- `DEPLOYMENT_DIR` - Target directory
- `DEEPSEEK_API_KEY` - API key from secrets
- `SECRET_KEY` - JWT secret from secrets

#### 3. Deployment Script Execution

Runs on Mac mini:
```bash
cd ~/AiChatBot
git fetch origin
git reset --hard origin/main
git clean -fd
./deployment/deploy-pm2.sh
```

#### 4. Verification

Checks service health:
- Backend health endpoint
- Frontend serving
- Gateway responding
- PM2 process status

#### 5. Notifications

Reports deployment status:
- Success: Green checkmark with summary
- Failure: Red X with error logs

---

## 🔑 GitHub Secrets Setup

### Complete Secrets List

| Secret | Purpose | Example | Required |
|--------|---------|---------|----------|
| `MAC_MINI_HOST` | Mac mini IP/hostname | `24.19.48.87` | Yes |
| `MAC_MINI_USER` | SSH username | `xuzhi` | Yes |
| `MAC_MINI_SSH_KEY` | SSH private key | See below | Yes |
| `MAC_MINI_SSH_PORT` | SSH port | `22` | No (defaults to 22) |
| `DEEPSEEK_API_KEY` | DeepSeek API key | `sk-xxx...` | Yes |
| `SECRET_KEY` | JWT secret | Random hex string | Yes |

### Step-by-Step Secret Configuration

#### 1. Generate SSH Key (Mac mini)

```bash
ssh-keygen -t ed25519 -C "github-actions-aichatbot" -f ~/.ssh/aichatbot_deploy
```

#### 2. Add Public Key to Authorized Keys

```bash
cat ~/.ssh/aichatbot_deploy.pub >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

#### 3. Get Private Key

```bash
cat ~/.ssh/aichatbot_deploy
```

Copy the entire output including:
```
-----BEGIN OPENSSH PRIVATE KEY-----
...your key content...
-----END OPENSSH PRIVATE KEY-----
```

#### 4. Add Secrets to GitHub

**Via GitHub Web UI:**

1. Go to: https://github.com/GeorgeZhiXu/AiChatBot/settings/secrets/actions
2. Click "New repository secret"
3. Add each secret:
   - Name: `MAC_MINI_HOST`
   - Value: `24.19.48.87`
   - Click "Add secret"
4. Repeat for all 6 secrets

**Via GitHub CLI:**

```bash
# SSH configuration
gh secret set MAC_MINI_HOST --body "24.19.48.87"
gh secret set MAC_MINI_USER --body "xuzhi"
gh secret set MAC_MINI_SSH_KEY --body "$(cat ~/.ssh/aichatbot_deploy)"
gh secret set MAC_MINI_SSH_PORT --body "22"

# Application configuration
gh secret set DEEPSEEK_API_KEY --body "sk-your-api-key"
gh secret set SECRET_KEY --body "$(openssl rand -hex 32)"
```

#### 5. Verify Secrets

```bash
gh secret list

# Output:
# DEEPSEEK_API_KEY  Updated 2025-12-08
# MAC_MINI_HOST     Updated 2025-12-08
# MAC_MINI_SSH_KEY  Updated 2025-12-07
# MAC_MINI_USER     Updated 2025-12-07
# SECRET_KEY        Updated 2025-12-08
```

---

## 🚀 Using GitHub Actions

### Automatic Deployment

Just push your code:

```bash
git add .
git commit -m "Add new feature"
git push origin main
```

GitHub Actions automatically:
1. Detects push to main
2. Starts workflow
3. Deploys to Mac mini
4. Reports results

### Manual Deployment

Trigger deployment without code changes:

**Via GitHub Web UI:**
1. Go to: https://github.com/GeorgeZhiXu/AiChatBot/actions
2. Select "Deploy to Mac Mini (PM2 + Gateway)"
3. Click "Run workflow"
4. Select branch: `main`
5. Click "Run workflow"

**Via GitHub CLI:**
```bash
gh workflow run deploy-pm2.yml
```

### Monitor Deployment

**Real-time monitoring:**
```bash
# List recent runs
gh run list --limit 5

# Watch current run
gh run watch

# View specific run
gh run view <run-id>

# View logs
gh run view <run-id> --log

# View only failed logs
gh run view <run-id> --log-failed
```

**Via GitHub Web UI:**
- Go to: https://github.com/GeorgeZhiXu/AiChatBot/actions
- Click on latest workflow run
- View logs and status

### Deployment Duration

Typical deployment takes:
- **Fast**: 20-30 seconds (no npm install needed)
- **Full**: 60-90 seconds (fresh npm install)

Breakdown:
- Checkout code: 2-3s
- SSH connection: 1-2s
- Git pull: 2-3s
- Backend deploy: 5-10s
- Frontend build: 5-10s
- PM2 restart: 2-3s
- Health checks: 5s

---

## 📊 Workflow Logs & Debugging

### Understanding Workflow Logs

Logs are organized by steps:

1. **Set up job**: GitHub runner initialization
2. **Checkout code**: Git clone
3. **Deploy to Mac Mini via SSH**: Main deployment
4. **Send deployment notification**: Status report
5. **Deployment summary**: Final summary

### Reading Deployment Logs

**Color codes in logs:**
- 🟢 Green: Success messages
- 🟡 Yellow: Info/progress messages
- 🔴 Red: Errors/warnings

**Log sections:**
```
========================================
🚀 AiChatBot Deployment Starting
========================================

[i] Starting AiChatBot PM2 deployment...
[i] Creating directory structure...
[i] Creating backup...
[✓] Backup created: aichatbot-backup-20251208-120000.tar.gz
[i] Deploying backend...
[✓] Using existing .env file
[i] Installing Python dependencies...
[i] Building frontend...
[i] Deploying frontend...
[✓] AiChatBot routes added to nginx config
[i] Managing PM2 processes...
[✓] Backend is responding on port 8030
[✓] Frontend is responding on port 3030
[✓] Deployment completed successfully!
```

### Common Log Messages

**Success Indicators:**
```
[✓] Deployment completed successfully!
✓ Backend is healthy (port 8030)
✓ Frontend is serving (port 3030)
✓ Gateway is responding
```

**Warning Indicators:**
```
[!] .env file created but needs configuration
⚠ Gateway check failed (may need manual nginx restart)
```

**Error Indicators:**
```
[✗] Backend health check failed
❌ AiChatBot directory not found
Process exited with status 1
```

---

## 🐛 Troubleshooting GitHub Actions

### Problem: Workflow Fails Immediately

**Error**: "Error: Unable to connect to SSH server"

**Causes:**
- Incorrect SSH host/port
- SSH key not authorized
- Mac mini not reachable

**Solution:**
```bash
# Test SSH connection manually
ssh -i ~/.ssh/aichatbot_deploy xuzhi@24.19.48.87

# Check SSH service on Mac mini
sudo systemsetup -getremotelogin
# Should show: "Remote Login: On"

# Enable if needed
sudo systemsetup -setremotelogin on

# Verify secret is set
gh secret list | grep MAC_MINI_HOST
```

---

### Problem: "npm: command not found"

**Cause**: PATH not set in SSH session

**Solution**: Already fixed in workflow with:
```bash
export PATH="/opt/homebrew/bin:/usr/local/bin:$HOME/.nvm/versions/node/$(ls $HOME/.nvm/versions/node | tail -1)/bin:$PATH"
```

---

### Problem: "sudo: a password is required"

**Cause**: Attempting to run sudo commands in non-interactive SSH

**Solution**: Already fixed - `pm2 startup` skipped in CI environment

---

### Problem: Backend Health Check Fails

**Error**: "Backend health check failed"

**Causes:**
1. Port 8030 already in use
2. Python dependencies failed to install
3. .env file missing/incorrect

**Debug:**
```bash
# SSH into Mac mini
ssh xuzhi@24.19.48.87

# Check what's on port 8030
lsof -i :8030

# Check PM2 status
pm2 list | grep aichatbot

# View backend logs
pm2 logs aichatbot-backend --lines 50

# Check .env file
cat /Users/xuzhi/prod/aichatbot/backend/.env

# Test backend manually
cd /Users/xuzhi/prod/aichatbot/backend
source .venv/bin/activate
uvicorn main:asgi_app --host 0.0.0.0 --port 8030
```

---

### Problem: Secrets Not Working

**Error**: Backend logs show "DEEPSEEK_API_KEY: NOT SET!"

**Causes:**
1. Secrets not configured in GitHub
2. Secret names mismatch
3. `envs:` parameter missing in workflow

**Solution:**
```bash
# Verify secrets exist
gh secret list

# Check workflow has envs parameter
grep -A 3 "envs:" .github/workflows/deploy-pm2.yml
# Should include: DEEPSEEK_API_KEY,SECRET_KEY

# Update secret
gh secret set DEEPSEEK_API_KEY --body "sk-new-key"

# Trigger new deployment
git commit --allow-empty -m "test secrets"
git push origin main
```

---

## 📈 Monitoring Workflows

### GitHub Actions Dashboard

View at: https://github.com/GeorgeZhiXu/AiChatBot/actions

**Filters:**
- ✅ Success: Green checkmark
- ❌ Failure: Red X
- 🟡 In Progress: Yellow circle
- ⚫ Cancelled: Gray circle

### Email Notifications

GitHub automatically sends email notifications for:
- ❌ Failed workflows
- ✅ Fixed workflows (after failure)

Configure in: Settings → Notifications

### Deployment History

```bash
# View recent deployments
gh run list --limit 10

# View specific deployment
gh run view <run-id>

# Download logs
gh run view <run-id> --log > deployment.log

# Re-run failed deployment
gh run rerun <run-id>
```

---

## 🔄 Workflow Customization

### Skip Deployment for Docs

Already configured to skip deployment when only documentation changes:

```yaml
paths-ignore:
  - 'README.md'
  - 'docs/**'
  - '**.md'
```

### Add Deployment Notifications

Extend workflow to notify Slack, Discord, etc:

```yaml
- name: Notify Slack
  if: always()
  uses: slackapi/slack-github-action@v1
  with:
    payload: |
      {
        "text": "Deployment ${{ job.status }}"
      }
```

### Add Tests Before Deployment

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run tests
        run: |
          cd backend
          pip install -r requirements.txt
          pytest

  deploy:
    needs: test
    runs-on: ubuntu-latest
    # ... existing deployment steps
```

---

## 🎯 Best Practices

### Commit Messages

Good commit messages trigger clear deployment logs:

✅ **Good:**
```bash
git commit -m "Add message editing feature"
git commit -m "Fix Socket.IO reconnection bug"
git commit -m "Update DeepSeek API integration"
```

❌ **Avoid:**
```bash
git commit -m "fix"
git commit -m "updates"
git commit -m "wip"
```

### Deployment Safety

**Before pushing:**
1. Test locally with `npm run dev`
2. Build frontend locally: `npm run build`
3. Check for console errors
4. Verify API endpoints work

**After pushing:**
1. Monitor GitHub Actions run
2. Check deployment summary
3. Verify application works: http://24.19.48.87/aichatbot/
4. Check PM2 logs: `pm2 logs aichatbot`

### Rollback Strategy

If deployment breaks production:

**Option 1: Revert commit**
```bash
# On dev machine
git revert HEAD
git push origin main
# Triggers automatic re-deployment
```

**Option 2: Rollback to previous commit**
```bash
git reset --hard HEAD~1
git push origin main --force
# Triggers deployment to previous version
```

**Option 3: Manual rollback on Mac mini**
```bash
# SSH to Mac mini
cd ~/AiChatBot
git reset --hard <previous-commit-hash>
./deployment/deploy-pm2.sh
```

---

## 🔍 Debugging Failed Deployments

### Step-by-Step Debug Process

1. **Check workflow status**
   ```bash
   gh run list --limit 3
   ```

2. **View failed logs**
   ```bash
   gh run view <run-id> --log-failed
   ```

3. **Identify error section**
   - Look for `[✗]` or red error messages
   - Note the step that failed

4. **SSH to Mac mini and investigate**
   ```bash
   ssh xuzhi@24.19.48.87
   pm2 list
   pm2 logs aichatbot --lines 50
   ```

5. **Fix and redeploy**
   - Fix issue locally
   - Commit and push
   - Monitor new deployment

### Common Failure Patterns

**Pattern 1: "Permission denied"**
```
Permission denied (publickey)
```
**Fix**: Update `MAC_MINI_SSH_KEY` secret

**Pattern 2: "Port already in use"**
```
ERROR: address already in use
```
**Fix**: Kill old processes on Mac mini

**Pattern 3: "Command not found"**
```
npm: command not found
pm2: command not found
```
**Fix**: PATH issue - already fixed in workflow

**Pattern 4: "Health check failed"**
```
✗ Backend health check failed
```
**Fix**: Check PM2 logs for backend errors

---

## 📞 Getting Help

### Useful Links

- **Workflow runs**: https://github.com/GeorgeZhiXu/AiChatBot/actions
- **Repository settings**: https://github.com/GeorgeZhiXu/AiChatBot/settings
- **Secrets**: https://github.com/GeorgeZhiXu/AiChatBot/settings/secrets/actions
- **GitHub Actions docs**: https://docs.github.com/en/actions

### Debug Information to Collect

When asking for help, provide:

```bash
# GitHub Actions
gh run view <run-id> --log > workflow.log

# Mac mini status
ssh xuzhi@24.19.48.87 "pm2 list && pm2 logs aichatbot --lines 50" > macmini.log

# Secrets status (don't share values!)
gh secret list > secrets-list.txt

# Network test
curl -v http://24.19.48.87/health > network-test.txt 2>&1
```

---

## ✅ Success Indicators

After successful deployment, you should see:

**In GitHub Actions:**
```
✅ Deployment Completed Successfully!
✓ Backend is healthy (port 8030)
✓ Frontend is serving (port 3030)
✓ Gateway is responding
```

**On Mac mini:**
```bash
pm2 list
# Both aichatbot processes show "online" status

curl http://localhost:8030/health
# {"status":"healthy","users_online":0,"ai_processing":false}
```

**In browser:**
- http://24.19.48.87/aichatbot/ loads successfully
- Can register and login
- Chat connects immediately

---

## 🎓 Advanced Topics

### Multi-Environment Deployments

To deploy to staging and production:

1. Create separate branches: `staging`, `production`
2. Duplicate workflow file: `deploy-staging.yml`
3. Use different secrets: `STAGING_HOST`, `PROD_HOST`
4. Deploy to different directories

### Deployment Approvals

Add manual approval before production:

```yaml
jobs:
  deploy:
    environment:
      name: production
      url: http://24.19.48.87/aichatbot/
    # ... rest of job
```

Configure environment protection rules in Settings → Environments.

### Deployment Notifications

Add Slack/Discord webhook:

```yaml
- name: Notify on deployment
  if: always()
  run: |
    curl -X POST ${{ secrets.SLACK_WEBHOOK }} \
      -H 'Content-Type: application/json' \
      -d '{"text":"Deployment ${{ job.status }}"}'
```

---

## 📝 Workflow Maintenance

### Updating Secrets

When secrets change:

```bash
# Update single secret
gh secret set DEEPSEEK_API_KEY --body "sk-new-key"

# Trigger deployment to use new secret
git commit --allow-empty -m "Update secrets"
git push origin main
```

### Updating SSH Keys

```bash
# Generate new key
ssh-keygen -t ed25519 -C "github-new-key" -f ~/.ssh/aichatbot_new

# Add to authorized_keys
cat ~/.ssh/aichatbot_new.pub >> ~/.ssh/authorized_keys

# Update GitHub secret
gh secret set MAC_MINI_SSH_KEY --body "$(cat ~/.ssh/aichatbot_new)"

# Test deployment
git push origin main
```

### Updating IP Address

When your public IP changes:

```bash
# Update secret
gh secret set MAC_MINI_HOST --body "new.ip.address"

# Test
git commit --allow-empty -m "test new IP"
git push origin main
```

---

## 🎉 Summary

GitHub Actions provides:
- ✅ **Zero-touch deployments** - Just push code
- ✅ **Automatic .env management** - Secrets injected automatically
- ✅ **Health verification** - Ensures services are working
- ✅ **Deployment history** - Track all deployments
- ✅ **Rollback capability** - Easy to revert
- ✅ **Security** - Secrets encrypted and masked

**Your deployment is now fully automated!** 🚀
