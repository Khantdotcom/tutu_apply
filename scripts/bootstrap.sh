#!/usr/bin/env bash
set -euo pipefail

pnpm install
python3 -m venv apps/api/.venv
source apps/api/.venv/bin/activate
pip install -r apps/api/requirements.txt

echo "Bootstrap complete."
