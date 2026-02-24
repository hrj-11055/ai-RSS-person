#!/bin/bash
# AI-RSS-PERSON 服务器部署脚本
# 用途: 将本地代码部署到云服务器

set -e

# ================= 配置区域 =================
# 服务器信息
SERVER_HOST="8.135.37.159"
SERVER_USER="root"
SERVER_PORT="22"

# 项目路径
LOCAL_PROJECT_DIR="/Users/MarkHuang/ai-RSS-person"
REMOTE_PROJECT_DIR="/opt/ai-RSS-person"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ================= 函数 =================
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查本地环境
check_local_env() {
    log_info "检查本地环境..."

    if [ ! -d "$LOCAL_PROJECT_DIR" ]; then
        log_error "项目目录不存在: $LOCAL_PROJECT_DIR"
        exit 1
    fi

    if ! command -v rsync &> /dev/null; then
        log_error "rsync 未安装"
        exit 1
    fi

    log_info "本地环境检查通过"
}

# 测试服务器连接
test_connection() {
    log_info "测试服务器连接..."

    if ssh -p "${SERVER_PORT}" "${SERVER_USER}@${SERVER_HOST}" "echo 'Connection OK'" > /dev/null 2>&1; then
        log_info "服务器连接成功"
    else
        log_error "无法连接到服务器 ${SERVER_USER}@${SERVER_HOST}:${SERVER_PORT}"
        exit 1
    fi
}

# 上传代码
upload_code() {
    log_info "上传代码到服务器..."

    rsync -avz --delete \
        -e "ssh -p ${SERVER_PORT}" \
        --exclude='.git' \
        --exclude='__pycache__' \
        --exclude='*.pyc' \
        --exclude='reports/*.json' \
        --exclude='.venv' \
        --exclude='node_modules' \
        --exclude='scripts/mac' \
        --exclude='*.log' \
        "${LOCAL_PROJECT_DIR}/" \
        "${SERVER_USER}@${SERVER_HOST}:${REMOTE_PROJECT_DIR}/"

    log_info "代码上传完成"
}

# 创建远程目录
create_remote_dirs() {
    log_info "创建远程目录..."

    ssh -p "${SERVER_PORT}" "${SERVER_USER}@${SERVER_HOST}" << 'ENDSSH'
        mkdir -p /opt/ai-RSS-person/reports
        mkdir -p /opt/ai-RSS-person/logs
        chmod +x /opt/ai-RSS-person/scripts/server/*.sh
ENDSSH

    log_info "远程目录创建完成"
}

# 安装 Python 依赖
install_dependencies() {
    log_info "安装 Python 依赖..."

    ssh -p "${SERVER_PORT}" "${SERVER_USER}@${SERVER_HOST}" << 'ENDSSH'
        cd /opt/ai-RSS-person
        pip3 install -r requirements.txt 2>&1 | grep -E "(Successfully|already|Requirement)"
ENDSSH

    log_info "Python 依赖安装完成"
}

# 安装 systemd 服务
install_services() {
    log_info "安装 systemd 服务..."

    # 复制服务文件
    scp -P "${SERVER_PORT}" \
        "${LOCAL_PROJECT_DIR}/scripts/server/ai-rss-daily.service" \
        "${LOCAL_PROJECT_DIR}/scripts/server/ai-rss-daily.timer" \
        "${SERVER_USER}@${SERVER_HOST}:/etc/systemd/system/"

    # 重载并启用服务
    ssh -p "${SERVER_PORT}" "${SERVER_USER}@${SERVER_HOST}" << 'ENDSSH'
        systemctl daemon-reload
        systemctl enable ai-rss-daily.timer
        systemctl start ai-rss-daily.timer
        echo "服务状态:"
        systemctl status ai-rss-daily.timer --no-pager
ENDSSH

    log_info "systemd 服务安装完成"
}

# 设置时区
set_timezone() {
    log_info "设置服务器时区为 Asia/Shanghai..."

    ssh -p "${SERVER_PORT}" "${SERVER_USER}@${SERVER_HOST}" << 'ENDSSH'
        timedatectl set-timezone Asia/Shanghai
        echo "当前时区:"
        timedatectl | grep "Time zone"
ENDSSH

    log_info "时区设置完成"
}

# 显示部署后信息
show_post_deploy_info() {
    log_info "部署完成！"
    echo ""
    echo "==================== 部署信息 ===================="
    echo "服务器: ${SERVER_USER}@${SERVER_HOST}:${SERVER_PORT}"
    echo "项目目录: ${REMOTE_PROJECT_DIR}"
    echo ""
    echo "后续操作:"
    echo "1. 配置 .env 文件:"
    echo "   ssh ${SERVER_USER}@${SERVER_HOST}"
    echo "   vim ${REMOTE_PROJECT_DIR}/.env"
    echo ""
    echo "2. 启动 RSSHub:"
    echo "   bash ${REMOTE_PROJECT_DIR}/scripts/server/start-rsshub-server.sh"
    echo ""
    echo "3. 手动运行测试:"
    echo "   cd ${REMOTE_PROJECT_DIR}"
    echo "   python3 daily_report_PRO_cloud.py"
    echo ""
    echo "4. 查看定时任务状态:"
    echo "   systemctl status ai-rss-daily.timer"
    echo "   systemctl list-timers ai-rss-daily.timer"
    echo ""
    echo "5. 查看日志:"
    echo "   journalctl -u ai-rss-daily.service -f"
    echo "=================================================="
}

# ================= 主流程 =================
main() {
    echo "=========================================="
    echo "   AI-RSS-PERSON 服务器部署脚本"
    echo "=========================================="
    echo ""

    check_local_env
    test_connection
    create_remote_dirs
    upload_code
    install_dependencies
    install_services
    set_timezone
    show_post_deploy_info
}

# 执行主流程
main
