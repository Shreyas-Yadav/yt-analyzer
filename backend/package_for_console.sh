#!/bin/bash

# 1. Clean up previous builds
rm -rf package
rm -f lambda_function.zip

# 2. Install dependencies
echo "⬇️ Installing dependencies..."
mkdir package

# Install dependencies into package directory
# We use pip to install into a local 'package' dir, targeting Linux
uv pip install pip
python3 -m pip install \
    --platform manylinux2014_x86_64 \
    --target ./package \
    --implementation cp \
    --python-version 3.12 \
    --only-binary=:all: \
    --upgrade \
    fastapi uvicorn mangum sqlalchemy pymysql python-dotenv requests pydantic pydantic-core anthropic deep-translator

# 3. Zip dependencies
echo "🤐 Zipping dependencies..."
cd package
zip -r ../lambda_function.zip .
cd ..

# 4. Add application code
echo "📄 Adding application code..."
zip -g lambda_function.zip main.py
zip -g -r lambda_function.zip src

# 5. Cleanup
rm -rf package

echo "✅ Done! Upload 'lambda_function.zip' to AWS Lambda."
