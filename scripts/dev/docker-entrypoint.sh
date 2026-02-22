#!/bin/sh
set -e

# 设置 NODE_OPTIONS 以预加载 global-agent
export NODE_OPTIONS="-r /usr/local/lib/node_modules/global-agent/dist/src/index.js --max-http-header-size=32768"

# 设置 global-agent 代理配置
export GLOBAL_AGENT_HTTP_PROXY=${GLOBAL_AGENT_HTTP_PROXY:-http://0.250.250.254:7897}
export GLOBAL_AGENT_HTTPS_PROXY=${GLOBAL_AGENT_HTTPS_PROXY:-http://0.250.250.254:7897}

# 执行传入的命令
exec "$@"
