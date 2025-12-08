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
        PATH: '/Users/xuzhi/prod/aichatbot/backend/.venv/bin:/usr/local/bin:/usr/bin:/bin'
      },
      env_file: '/Users/xuzhi/prod/aichatbot/backend/.env',
      error_file: '/Users/xuzhi/prod/aichatbot/logs/backend-error.log',
      out_file: '/Users/xuzhi/prod/aichatbot/logs/backend-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      merge_logs: true,
      min_uptime: '10s',
      max_restarts: 10
    },
    {
      name: 'aichatbot-frontend',
      cwd: '/Users/xuzhi/prod/aichatbot/frontend',
      script: 'npx',
      args: 'serve -s dist -l 3030',
      interpreter: 'none',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '300M',
      env: {
        NODE_ENV: 'production'
      },
      error_file: '/Users/xuzhi/prod/aichatbot/logs/frontend-error.log',
      out_file: '/Users/xuzhi/prod/aichatbot/logs/frontend-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      merge_logs: true,
      min_uptime: '10s',
      max_restarts: 10
    }
  ]
};
