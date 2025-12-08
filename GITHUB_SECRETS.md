# GitHub Secrets Configuration

This document lists all the GitHub Secrets you need to configure for automated PM2 deployment.

## Required Secrets

Go to your repository settings to add these secrets:
`https://github.com/GeorgeZhiXu/AiChatBot/settings/secrets/actions`

### 1. SSH Connection Secrets

| Secret Name | Description | Example |
|-------------|-------------|---------|
| `MAC_MINI_HOST` | IP address or hostname of your Mac mini | `24.19.51.52` or `xuzhi.ddns.net` |
| `MAC_MINI_USER` | Username on your Mac mini | `xuzhi` |
| `MAC_MINI_SSH_KEY` | Private SSH key for authentication | Contents of `~/.ssh/id_ed25519` |
| `MAC_MINI_SSH_PORT` | SSH port (optional, defaults to 22) | `22` |

### 2. Application Secrets

| Secret Name | Description | How to Get |
|-------------|-------------|------------|
| `DEEPSEEK_API_KEY` | DeepSeek API key for AI features | Get from https://platform.deepseek.com |
| `SECRET_KEY` | JWT secret key for authentication | Generate with: `openssl rand -hex 32` |

## Setup Instructions

### Step 1: Generate SSH Key (if needed)

```bash
# On your Mac mini
ssh-keygen -t ed25519 -C "github-actions-aichatbot" -f ~/.ssh/aichatbot_deploy

# Add public key to authorized_keys
cat ~/.ssh/aichatbot_deploy.pub >> ~/.ssh/authorized_keys

# Copy private key for GitHub secret
cat ~/.ssh/aichatbot_deploy
# Copy the entire output including -----BEGIN and -----END lines
```

### Step 2: Get DeepSeek API Key

1. Visit https://platform.deepseek.com
2. Sign up or log in
3. Navigate to API Keys section
4. Create a new API key
5. Copy the key (starts with `sk-`)

### Step 3: Generate SECRET_KEY

```bash
# Generate a secure random secret
openssl rand -hex 32
# or
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### Step 4: Add Secrets to GitHub

1. Go to: https://github.com/GeorgeZhiXu/AiChatBot/settings/secrets/actions
2. Click "New repository secret"
3. Add each secret one by one:

**SSH Secrets:**
- Name: `MAC_MINI_HOST`, Value: Your Mac mini IP (e.g., `24.19.51.52`)
- Name: `MAC_MINI_USER`, Value: Your username (e.g., `xuzhi`)
- Name: `MAC_MINI_SSH_KEY`, Value: Paste entire private key content
- Name: `MAC_MINI_SSH_PORT`, Value: `22` (optional)

**Application Secrets:**
- Name: `DEEPSEEK_API_KEY`, Value: Your DeepSeek API key
- Name: `SECRET_KEY`, Value: Generated secret from Step 3

### Step 5: Verify Setup

After adding all secrets, push a commit to trigger deployment:

```bash
git add .
git commit -m "test deployment"
git push origin main
```

The GitHub Actions workflow will:
1. SSH into your Mac mini
2. Pull latest code
3. Create/update `.env` with your secrets
4. Deploy and start services
5. Verify deployment

## Security Notes

- **Never commit secrets** to the repository
- Secrets are encrypted by GitHub
- Secrets are only accessible during workflow execution
- Secrets are masked in logs (shown as `***`)
- Rotate your secrets regularly
- Use least-privilege SSH keys

## Updating Secrets

When you need to change API keys or secrets:

1. Go to: https://github.com/GeorgeZhiXu/AiChatBot/settings/secrets/actions
2. Click on the secret name
3. Click "Update secret"
4. Enter new value
5. Save

The next deployment will automatically use the updated secrets.

## Manual Override

If you prefer to manage `.env` manually on the Mac mini:

1. SSH into your Mac mini
2. Edit the file: `nano /Users/xuzhi/prod/aichatbot/backend/.env`
3. Make your changes
4. Restart backend: `pm2 restart aichatbot-backend`

**Note:** Manual changes will be overwritten if GitHub Secrets are set. To prevent this, remove the secrets from GitHub.

## Troubleshooting

### Deployment fails with "Permission denied"

- Check if `MAC_MINI_SSH_KEY` contains the complete private key
- Verify the public key is in `~/.ssh/authorized_keys` on Mac mini
- Check SSH service is running: `sudo systemsetup -getremotelogin`

### Backend fails with authentication errors

- Verify `DEEPSEEK_API_KEY` is correct
- Check API key has sufficient credits
- View backend logs: `pm2 logs aichatbot-backend`

### Changes not taking effect

- Secrets are only loaded during deployment
- Push a new commit or manually trigger workflow
- Check workflow run logs for errors

## Support

For issues with:
- **GitHub Secrets**: Check GitHub documentation
- **Deployment**: Review GitHub Actions logs
- **Application**: Check PM2 logs with `pm2 logs aichatbot`
