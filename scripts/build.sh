#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ -f package.json ]] && command -v npm >/dev/null 2>&1; then
  npm run build
fi

if [[ -f pyproject.toml ]]; then
  python3 -m compileall agents
elif [[ -d agents ]]; then
  python3 -m compileall agents
fi

echo "Build complete"
