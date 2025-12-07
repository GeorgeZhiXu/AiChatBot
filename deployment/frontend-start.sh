#!/bin/bash
# Frontend startup script for Mac mini deployment
# Port: 3030

set -e

# Configuration
APP_DIR="$HOME/AiChatBot"
FRONTEND_DIR="$APP_DIR/frontend"
PORT=3030

# Navigate to frontend directory
cd "$FRONTEND_DIR"

# Use built files or run preview server
if [ -d "dist" ]; then
    echo "[Frontend] Serving built files on port $PORT..."
    npx serve -s dist -l "$PORT"
else
    echo "[Frontend] Running dev server on port $PORT..."
    npm run dev -- --host --port "$PORT"
fi
