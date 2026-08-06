#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

mkdir -p .local/audit-logs

if [[ ! -f .env && -f .env.example ]]; then
  cp .env.example .env
  echo "Created .env from .env.example"
fi

if command -v python3 >/dev/null 2>&1; then
  if [[ ! -d apps/backend/.venv ]]; then
    python3 -m venv apps/backend/.venv
    echo "Created apps/backend/.venv"
  fi
  apps/backend/.venv/bin/python -m pip install --upgrade pip >/dev/null
  apps/backend/.venv/bin/python -m pip install -r apps/backend/requirements.txt
fi

if [[ -f package.json ]] && command -v npm >/dev/null 2>&1; then
  npm install
fi

echo "Setup complete"
