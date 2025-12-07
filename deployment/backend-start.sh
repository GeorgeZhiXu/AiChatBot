#!/bin/bash
# Backend startup script for Mac mini deployment
# Port: 8030

set -e

# Configuration
APP_DIR="$HOME/AiChatBot"
BACKEND_DIR="$APP_DIR/backend"
VENV_DIR="$BACKEND_DIR/.venv"
PORT=8030

# Load environment variables
if [ -f "$BACKEND_DIR/.env" ]; then
    export $(cat "$BACKEND_DIR/.env" | grep -v '^#' | xargs)
fi

# Navigate to backend directory
cd "$BACKEND_DIR"

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Start backend server
echo "[Backend] Starting AI Group Chat Backend on port $PORT..."
uvicorn main:asgi_app --host 0.0.0.0 --port "$PORT" --workers 1
