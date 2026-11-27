#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

if [ ! -x ".venv/bin/python" ]; then
  echo "[1/2] Dang tao moi truong .venv..."
  python3 -m venv .venv
  echo "[2/2] Dang cai numpy..."
  .venv/bin/python -m pip install --quiet numpy
fi

if [ -f "checkpoints/cnn_9x9.pt" ]; then
  .venv/bin/python -c "import torch" >/dev/null 2>&1 || \
    .venv/bin/python -m pip install --quiet torch --index-url https://download.pytorch.org/whl/cpu
fi

exec .venv/bin/python -X utf8 -m ui.web_app "$@"
