#!/usr/bin/env bash
# MindWall — One-Command Setup
# Developed by Pradyumn Tandon (https://pradyumntandon.com) at VRIP7 (https://vrip7.com)

set -euo pipefail

echo "[MindWall] Checking dependencies..."
command -v docker >/dev/null 2>&1 || { echo "Docker required."; exit 1; }
command -v docker compose >/dev/null 2>&1 || { echo "Docker Compose required."; exit 1; }
nvidia-smi >/dev/null 2>&1 || { echo "NVIDIA GPU + drivers required."; exit 1; }

echo "[MindWall] Generating secrets..."
cp -n .env.example .env 2>/dev/null || true
SECRET=$(openssl rand -hex 32)
sed -i "s|API_SECRET_KEY=.*|API_SECRET_KEY=${SECRET}|" .env

echo "[MindWall] Creating data directories..."
mkdir -p data/db data/models

echo "[MindWall] Building and starting services..."
docker compose up -d --build

echo "[MindWall] Waiting for Ollama to be healthy..."
until docker compose exec ollama curl -sf http://localhost:11434/api/tags > /dev/null 2>&1; do
    echo "  Waiting for Ollama..."
    sleep 5
done

echo "[MindWall] Pulling LLM model (this may take a few minutes)..."
docker compose exec ollama ollama pull llama3.1:8b

echo ""
echo "✅ MindWall is running."
echo "   Dashboard:      http://localhost:3000"
echo "   API:            http://localhost:8000"
echo "   IMAP Proxy:     localhost:1143"
echo ""
echo "   Point your email client's IMAP server to: localhost:1143"
echo ""
echo "   Developed by Pradyumn Tandon (https://pradyumntandon.com) at VRIP7 (https://vrip7.com)"
