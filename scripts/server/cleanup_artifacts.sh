#!/bin/bash
# Cleanup old report artifacts to control disk growth.

set -euo pipefail

PROJECT_DIR="/opt/ai-RSS-person"
ENV_FILE="${PROJECT_DIR}/.env"

OUTPUT_DIR="${PROJECT_DIR}/reports"
PIPELINE_DIR="${OUTPUT_DIR}/.pipeline"
RETENTION_REPORT_DAYS="${RETENTION_REPORT_DAYS:-14}"
RETENTION_PIPELINE_DAYS="${RETENTION_PIPELINE_DAYS:-30}"

if [ -f "$ENV_FILE" ]; then
  env_output_dir=$(grep -E '^OUTPUT_DIR=' "$ENV_FILE" | tail -n1 | cut -d '=' -f2- || true)
  env_pipeline_dir=$(grep -E '^PIPELINE_CACHE_DIR=' "$ENV_FILE" | tail -n1 | cut -d '=' -f2- || true)
  env_retention_report=$(grep -E '^RETENTION_REPORT_DAYS=' "$ENV_FILE" | tail -n1 | cut -d '=' -f2- || true)
  env_retention_pipeline=$(grep -E '^RETENTION_PIPELINE_DAYS=' "$ENV_FILE" | tail -n1 | cut -d '=' -f2- || true)

  if [ -n "$env_output_dir" ]; then
    if [[ "$env_output_dir" = /* ]]; then
      OUTPUT_DIR="$env_output_dir"
    else
      OUTPUT_DIR="${PROJECT_DIR}/${env_output_dir}"
    fi
  fi

  if [ -n "$env_pipeline_dir" ]; then
    if [[ "$env_pipeline_dir" = /* ]]; then
      PIPELINE_DIR="$env_pipeline_dir"
    else
      PIPELINE_DIR="${PROJECT_DIR}/${env_pipeline_dir}"
    fi
  else
    PIPELINE_DIR="${OUTPUT_DIR}/.pipeline"
  fi

  [ -n "$env_retention_report" ] && RETENTION_REPORT_DAYS="$env_retention_report"
  [ -n "$env_retention_pipeline" ] && RETENTION_PIPELINE_DAYS="$env_retention_pipeline"
fi

echo "[cleanup] OUTPUT_DIR=$OUTPUT_DIR RETENTION_REPORT_DAYS=$RETENTION_REPORT_DAYS"
echo "[cleanup] PIPELINE_DIR=$PIPELINE_DIR RETENTION_PIPELINE_DAYS=$RETENTION_PIPELINE_DAYS"

if [ -d "$OUTPUT_DIR" ]; then
  find "$OUTPUT_DIR" -maxdepth 1 -type f \( -name '*.json' -o -name '*.md' -o -name '*.html' \) -mtime +"$RETENTION_REPORT_DAYS" -print -delete
fi

if [ -d "$PIPELINE_DIR" ]; then
  find "$PIPELINE_DIR" -maxdepth 1 -type f -mtime +"$RETENTION_PIPELINE_DAYS" -print -delete
fi

echo "[cleanup] done"
