#!/usr/bin/env bash
# package-dashboard.sh — Package the dashboard API as a Lambda zip (no Docker needed).
#
# Usage:  ./scripts/package-dashboard.sh
# Output: dist/dashboard-lambda.zip (ready to upload to Lambda)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BUILD_DIR="$PROJECT_ROOT/dist/dashboard-lambda"
OUTPUT_ZIP="$PROJECT_ROOT/dist/dashboard-lambda.zip"

echo "→ Cleaning build directory..."
rm -rf "$BUILD_DIR" "$OUTPUT_ZIP"
mkdir -p "$BUILD_DIR"

echo "→ Installing dependencies into build dir..."
pip install \
    --target "$BUILD_DIR" \
    --platform manylinux2014_x86_64 \
    --implementation cp \
    --python-version 3.11 \
    --only-binary=:all: \
    --no-deps \
    fastapi uvicorn mangum pydantic pydantic-settings pydantic-core \
    starlette anyio sniffio typing-extensions annotated-types \
    sqlalchemy psycopg2-binary python-dotenv click h11 httptools \
    idna certifi greenlet 2>/dev/null || true

# Some packages don't have manylinux wheels — install without platform constraint
pip install \
    --target "$BUILD_DIR" \
    --no-deps \
    fastapi uvicorn mangum pydantic pydantic-settings \
    starlette anyio sniffio typing-extensions annotated-types \
    sqlalchemy python-dotenv click h11 idna certifi 2>/dev/null || true

# psycopg2-binary needs the linux wheel specifically
pip install \
    --target "$BUILD_DIR" \
    --platform manylinux2014_x86_64 \
    --implementation cp \
    --python-version 3.11 \
    --only-binary=:all: \
    psycopg2-binary 2>/dev/null || true

echo "→ Copying application code..."
cp -r "$PROJECT_ROOT/dashboard"          "$BUILD_DIR/dashboard"
cp -r "$PROJECT_ROOT/db"                 "$BUILD_DIR/db"
cp    "$PROJECT_ROOT/config.py"          "$BUILD_DIR/"
cp    "$PROJECT_ROOT/logger.py"          "$BUILD_DIR/"
cp    "$PROJECT_ROOT/dashboard_handler.py" "$BUILD_DIR/"

# Remove __pycache__ and .pyc files
find "$BUILD_DIR" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "$BUILD_DIR" -name "*.pyc" -delete 2>/dev/null || true

echo "→ Creating zip..."
cd "$BUILD_DIR"
zip -r -q "$OUTPUT_ZIP" .

SIZE=$(du -h "$OUTPUT_ZIP" | cut -f1)
echo "✓ Package ready: dist/dashboard-lambda.zip ($SIZE)"
