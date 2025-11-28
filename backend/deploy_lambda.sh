#!/bin/bash
set -e

echo "🚀 Deploying to AWS Lambda..."

# 1. Install dependencies
echo "📦 Syncing dependencies..."
uv sync

# 2. Export requirements.txt (SAM needs this)
echo "📄 Generating requirements.txt..."
uv pip compile pyproject.toml -o requirements.txt

# 3. Build
echo "🏗️ Building..."
sam build

# 4. Deploy
echo "☁️ Deploying..."
sam deploy --guided \
  --stack-name yt-analyzer-backend \
  --capabilities CAPABILITY_IAM \
  --region us-east-1

echo "✅ Deployment Complete!"
