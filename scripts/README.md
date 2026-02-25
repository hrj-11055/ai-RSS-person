# Scripts 目录说明

本目录包含 AI-RSS-PERSON 项目的各种脚本，按平台分类。

## 目录结构

```
scripts/
├── dev/                    # 开发/通用脚本
│   ├── start.sh           # 本地启动
│   ├── stop.sh            # 本地停止
│   ├── send_report.sh     # 手动发送报告
│   ├── pre_pr_check.sh    # 提交前质量检查（测试+文档一致）
│   ├── check_docs_consistency.py  # 文档一致性检查
│   └── test_*.py          # 测试脚本
│
├── mac/                    # macOS 专用脚本
│   ├── update_twitter_cookie.sh    # 更新 Twitter Cookie
│   ├── manage_cron.sh             # 管理 cron 任务
│   └── daily_report_with_docker_check.sh  # 兼容旧文件名（实际执行 npm/service 检查）
│
└── server/                 # 服务器专用脚本
    ├── start-rsshub-server.sh      # 启动 RSSHub
    ├── ai-rss-daily.service        # systemd 服务配置
    ├── ai-rss-daily.timer          # systemd 定时器配置
    ├── ai-rss-cleanup.service      # 产物清理服务
    ├── ai-rss-cleanup.timer        # 产物清理定时器
    ├── cleanup_artifacts.sh        # 清理历史报告与缓存
    ├── ai-rss-cookie-rotate.service # Twitter Cookie 轮换服务
    ├── ai-rss-cookie-rotate.timer   # Twitter Cookie 每周轮换定时器
    ├── rotate_twitter_cookie.sh     # 轮换脚本（更新 .env 并重启 RSSHub）
    ├── check_email_delivery.sh      # 检查 JSON->MD->邮件发送链路
    ├── deploy.sh                   # 一键部署脚本
    └── health-check.sh             # 健康检查脚本
```

## 使用说明

### 本地开发 (macOS)

```bash
# 启动项目
./scripts/dev/start.sh

# 停止项目
./scripts/dev/stop.sh

# 更新 Twitter Cookie
./scripts/mac/update_twitter_cookie.sh

# 检查 README 与代码默认值是否一致
python3 ./scripts/dev/check_docs_consistency.py

# 提交前执行完整检查（推荐）
./scripts/dev/pre_pr_check.sh
```

### 服务器部署

```bash
# 一键部署到服务器
./scripts/server/deploy.sh

# 在服务器上检查健康状态
ssh root@8.135.37.159 "bash /opt/ai-RSS-person/scripts/server/health-check.sh"
```

### systemd 服务管理

```bash
# 查看定时任务状态
systemctl status ai-rss-daily.timer

# 查看下次执行时间
systemctl list-timers ai-rss-daily.timer

# 查看清理定时器状态
systemctl status ai-rss-cleanup.timer

# 查看 Cookie 轮换定时器状态
systemctl status ai-rss-cookie-rotate.timer

# 查看日志
journalctl -u ai-rss-daily.service -f

# 手动触发执行
systemctl start ai-rss-daily.service
```

## 迁移说明

- **macOS 脚本**: 使用 launchd 进行定时任务
- **服务器脚本**: 使用 systemd 进行定时任务
- **通用脚本**: scripts/dev/ 下的脚本在两种平台均可使用
