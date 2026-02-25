#!/bin/bash
# Check JSON -> Markdown -> Email delivery path on server.

set -euo pipefail

PROJECT_DIR="/opt/ai-RSS-person"
PYTHON_BIN="${PROJECT_DIR}/.venv/bin/python"

if [ ! -x "$PYTHON_BIN" ]; then
  echo "[ERROR] Python venv not found: $PYTHON_BIN"
  exit 1
fi

cd "$PROJECT_DIR"

if [ ! -f "$PROJECT_DIR/.env" ]; then
  echo "[ERROR] .env not found"
  exit 1
fi

set -a
source "$PROJECT_DIR/.env"
set +a

if [ "${EMAIL_ENABLED:-false}" != "true" ]; then
  echo "[ERROR] EMAIL_ENABLED is not true"
  exit 1
fi

echo "[check] running email pipeline: JSON -> MD -> SMTP"
"$PYTHON_BIN" daily_email_sender.py

echo "[check] email delivery pipeline succeeded"
