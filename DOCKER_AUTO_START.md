# Docker 自动启动功能

## 概述

为解决定时任务运行时 Docker 服务可能未启动的问题，创建了带 Docker 检查的启动脚本。

## 文件

- **[daily_report_with_docker_check.sh](daily_report_with_docker_check.sh)** - 新的启动脚本（带 Docker 检查）
- **[com.aireport.daily.plist](com.aireport.daily.plist)** - 已更新为使用新脚本

## 功能

启动脚本会自动：

1. ✅ **检查 Docker 服务状态**
   - 检查 RSSHub 容器
   - 检查 Redis 容器

2. 🔄 **自动启动未运行的 Docker 服务**
   - 如果服务未运行，执行 `docker compose up -d`
   - 等待 5 秒验证服务启动

3. ✅ **验证服务状态**
   - 确认 RSSHub 和 Redis 正常运行
   - 显示服务状态

4. ▶️ **运行主程序**
   - 执行日报生成脚本
   - 收集 RSS 源
   - AI 分析
   - 生成报告

## 更新定时任务

如需使用新的 Docker 检查功能，请更新定时任务配置：

```bash
# 1. 卸载旧任务
./manage_cron.sh uninstall

# 2. 编辑 plist 文件（可选）
# 将 ProgramArguments 从:
#   <string>/Users/MarkHuang/ai-RSS-person/daily_report_PRO_cloud.py</string>
# 改为:
#   <string>/Users/MarkHuang/ai-RSS-person/daily_report_with_docker_check.sh</string>

# 3. 重新安装
./manage_cron.sh install
```

## 使用方式

### 手动运行

```bash
# 直接运行（会自动检查 Docker）
./daily_report_with_docker_check.sh
```

### 定时任务运行

每天 7:00 AM 自动运行，会自动检查并启动 Docker 服务。

## 相关配置

- [`.env`](.env) - 环境变量配置
- [`.env.example`](.env.example) - 示例配置（已更新）
- [`docker-compose.yml`](docker-compose.yml) - Docker 服务配置

## 注意事项

1. **轻量部署**: 当前仅运行 RSSHub + Redis（~285 MB）
2. **MySQL + wewe-rss**: 已禁用以节省内存
3. **日志位置**: `logs/stdout.log` 和 `logs/stderr.log`
4. **报告输出**: `reports/` 目录
