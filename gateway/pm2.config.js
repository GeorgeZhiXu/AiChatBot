module.exports = {
  apps: [
    {
      name: 'aichatbot-backend',
      cwd: '/Users/xuzhi/prod/aichatbot/backend',
      script: '.venv/bin/uvicorn',
      args: 'main:asgi_app --host 0.0.0.0 --port 8030',
      interpreter: 'none',
      autorestart: true,
      watch: false,
      max_memory_restart: '500M',
      env_file: '/Users/xuzhi/prod/aichatbot/backend/.env',
      env: {
        PYTHONPATH: '/Users/xuzhi/prod/aichatbot/backend',
        PATH: '/Users/xuzhi/prod/aichatbot/backend/.venv/bin:/usr/local/bin:/usr/bin:/bin'
      },
      error_file: '/Users/xuzhi/prod/gateway/logs/aichatbot-backend-error.log',
      out_file: '/Users/xuzhi/prod/gateway/logs/aichatbot-backend-out.log',
      log_file: '/Users/xuzhi/prod/gateway/logs/aichatbot-backend.log',
      time: true,
      min_uptime: '10s',
      max_restarts: 10
    },
    {
      name: 'aichatbot-frontend',
      cwd: '/Users/xuzhi/prod/aichatbot/frontend',
      script: 'npx',
      args: 'serve -s dist -l 3030',
      interpreter: 'none',
      autorestart: true,
      watch: false,
      max_memory_restart: '300M',
      env: {
        NODE_ENV: 'production'
      },
      error_file: '/Users/xuzhi/prod/gateway/logs/aichatbot-frontend-error.log',
      out_file: '/Users/xuzhi/prod/gateway/logs/aichatbot-frontend-out.log',
      log_file: '/Users/xuzhi/prod/gateway/logs/aichatbot-frontend.log',
      time: true,
      min_uptime: '10s',
      max_restarts: 10
    }
  ]
};
