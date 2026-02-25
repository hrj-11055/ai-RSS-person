#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="/Users/MarkHuang/ai-RSS-person"
cd "$ROOT_DIR"

if [[ ! -f ".env.sim" ]]; then
  echo "[ERROR] .env.sim not found"
  exit 1
fi

set -a
source .env.sim
set +a

export PYTHONPATH="$ROOT_DIR:${PYTHONPATH:-}"

# 若 .env.sim 仍是占位 key，尝试复用本地 .env 的真实 key（仅覆盖该字段）
if [[ "${DEEPSEEK_API_KEY:-}" == "simulation_key_placeholder" || -z "${DEEPSEEK_API_KEY:-}" ]]; then
  if [[ -f ".env" ]]; then
    REAL_KEY="$(rg '^DEEPSEEK_API_KEY=' .env -N | tail -n 1 | cut -d '=' -f 2- || true)"
    if [[ -n "${REAL_KEY:-}" ]]; then
      export DEEPSEEK_API_KEY="$REAL_KEY"
      echo "[INFO] Using DEEPSEEK_API_KEY from .env for real-AI simulation."
    fi
  fi
fi

python3 daily_report_PRO_cloud.py
