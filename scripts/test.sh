#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

test -f README.md
test -f .env.example
test -f LICENSE
test -f docs/ethics-and-safety.md

python3 -m compileall agents
python3 agents/crewai_stub.py --objective "Plan defensive training lab" --scope "Owned local lab" >/dev/null
python3 agents/autogen_stub.py --objective "Prepare authorized audit checklist" --scope "Internal staging app" >/dev/null

if [[ -x apps/backend/.venv/bin/python ]]; then
  (cd apps/backend && .venv/bin/python -m pytest -q -s)
else
  echo "Missing apps/backend/.venv; run ./scripts/setup.sh first" >&2
  exit 1
fi

if command -v npm >/dev/null 2>&1; then
  npm --prefix apps/desktop run typecheck
else
  echo "Missing npm; cannot typecheck desktop app" >&2
  exit 1
fi

echo "Tests complete"
