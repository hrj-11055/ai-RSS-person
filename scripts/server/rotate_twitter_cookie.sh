#!/bin/bash
# Rotate Twitter auth credentials used by RSSHub.
# Reads a raw Cookie header string from a secure local file,
# extracts auth_token + ct0, updates .env, and restarts rsshub.

set -euo pipefail

PROJECT_DIR="/opt/ai-RSS-person"
ENV_FILE="${PROJECT_DIR}/.env"
LOG_FILE="${PROJECT_DIR}/logs/twitter-cookie-rotate.log"
COOKIE_SOURCE_FILE_DEFAULT="/opt/ai-RSS-person/secrets/twitter_cookie.txt"

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

get_env_value() {
  local key="$1"
  if [ -f "$ENV_FILE" ]; then
    grep -E "^${key}=" "$ENV_FILE" | tail -n1 | cut -d '=' -f2- || true
  fi
}

set_env_value() {
  local key="$1"
  local value="$2"

  touch "$ENV_FILE"
  chmod 600 "$ENV_FILE"

  if grep -qE "^${key}=" "$ENV_FILE"; then
    sed -i "s|^${key}=.*$|${key}=${value}|" "$ENV_FILE"
  else
    echo "${key}=${value}" >> "$ENV_FILE"
  fi
}

extract_cookie_field() {
  local raw_cookie="$1"
  local field="$2"
  echo "$raw_cookie" | sed 's/; /;/g' | tr ';' '\n' | sed 's/^ *//;s/ *$//' | grep -E "^${field}=" | head -n1 | cut -d '=' -f2-
}

main() {
  mkdir -p "$(dirname "$LOG_FILE")"

  if [ ! -f "$ENV_FILE" ]; then
    log "ERROR: .env not found at $ENV_FILE"
    exit 1
  fi

  local source_file
  source_file="$(get_env_value TWITTER_COOKIE_SOURCE_FILE)"
  source_file="${source_file:-$COOKIE_SOURCE_FILE_DEFAULT}"

  if [ ! -f "$source_file" ]; then
    log "ERROR: cookie source file not found: $source_file"
    exit 1
  fi

  local raw_cookie
  raw_cookie="$(cat "$source_file")"

  if [ -z "$raw_cookie" ]; then
    log "ERROR: cookie source content is empty"
    exit 1
  fi

  local new_auth_token
  local new_ct0
  new_auth_token="$(extract_cookie_field "$raw_cookie" "auth_token")"
  new_ct0="$(extract_cookie_field "$raw_cookie" "ct0")"

  if [ -z "$new_auth_token" ] || [ -z "$new_ct0" ]; then
    log "ERROR: failed to parse auth_token/ct0 from cookie source"
    exit 1
  fi

  local old_auth_token old_ct0
  old_auth_token="$(get_env_value TWITTER_AUTH_TOKEN)"
  old_ct0="$(get_env_value TWITTER_CT0)"

  if [ "$new_auth_token" = "$old_auth_token" ] && [ "$new_ct0" = "$old_ct0" ]; then
    log "INFO: cookie unchanged, skip restart"
    exit 0
  fi

  set_env_value "TWITTER_AUTH_TOKEN" "$new_auth_token"
  set_env_value "TWITTER_CT0" "$new_ct0"

  log "INFO: cookie rotated, restarting rsshub"
  cd "$PROJECT_DIR"
  docker compose up -d rsshub

  sleep 5
  if ! docker ps --format '{{.Names}}' | grep -q '^rss-person-rsshub$'; then
    log "ERROR: rsshub container is not running after restart"
    exit 1
  fi

  # Lightweight runtime check: route should be reachable (status 200 expected)
  if curl -fsS --max-time 20 "http://localhost:1200/twitter/user/OpenAI" >/dev/null 2>&1; then
    log "INFO: twitter route check passed"
  else
    log "WARN: twitter route check failed (may be transient/rate-limited)"
  fi

  log "INFO: rotate complete"
}

main "$@"
