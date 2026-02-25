#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

echo "==> [1/2] 运行单元测试"
python3 -m unittest discover tests -v

echo "==> [2/2] 检查文档一致性"
python3 scripts/dev/check_docs_consistency.py

echo "✅ pre-PR 检查通过"
