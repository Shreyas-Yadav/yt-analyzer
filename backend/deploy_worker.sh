#!/bin/bash

# Exit on error
set -e

echo "🚀 Starting Worker Deployment..."

# 1. Update System and Install System Dependencies
echo "📦 Installing system dependencies (ffmpeg)..."
sudo apt-get update
sudo apt-get install -y ffmpeg git

# 2. Install uv (Python package manager)
if ! command -v uv &> /dev/null; then
    echo "📦 Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    
    # Source the correct env file
    if [ -f "$HOME/.local/bin/env" ]; then
        source "$HOME/.local/bin/env"
    elif [ -f "$HOME/.cargo/env" ]; then
        source "$HOME/.cargo/env"
    fi
else
    echo "✅ uv is already installed"
fi

# 3. Sync Python Dependencies
echo "🐍 Installing Python dependencies..."
# Ensure we are in the directory with pyproject.toml
cd "$(dirname "$0")"
uv sync --extra worker

# 4. Check for .env file (Optional if using AWS SSM)
if [ ! -f .env ]; then
    echo "ℹ️  Note: .env file not found."
    echo "Ensure you have configured AWS SSM Parameter Store (/yt-analyzer/config) OR create a .env file."
fi

echo "🔄 Starting Worker (Foreground)..."
# Run directly in foreground so we can see output immediately
uv run worker.py
