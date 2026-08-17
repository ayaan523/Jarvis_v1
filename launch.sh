#!/usr/bin/env bash
set -euo pipefail
repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$repo_dir"
if [[ -x "$repo_dir/.venv/bin/python" ]]; then
  exec "$repo_dir/.venv/bin/python" main.py
fi
exec python3 main.py
