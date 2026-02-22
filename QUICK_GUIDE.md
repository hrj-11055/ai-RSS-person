# 快捷命令使用指南

## 概述

为了简化 Docker 服务管理，创建了以下快捷脚本：

- **start.sh** - 一键启动脚本（交互式）
- **stop.sh** - 快速停止脚本

## 使用方式

### 方式 1：一键启动（推荐）

```bash
./start.sh
```

**功能流程**：
1. ✅ 启动 Docker 服务（RSSHub + Redis）
2. 📊 等待服务启动（5秒）
3. 📋 显示服务状态
4. 🎯 选择操作：
   - **1** - 运行日报生成（完成后自动关闭服务）
   - **2** - 仅关闭服务
   - **3** - 保持运行

**适用场景**：
- 📅 日常使用（推荐）
- 🔄 测试配置
- 🧪 需要调试（保持运行）

### 方式 2：快速停止

```bash
./stop.sh
```

**功能**：
- ⚠️ 停止所有 Docker 服务
- 💾 释放内存（~285 MB）
- ✅ 适用于所有场景

**适用场景**：
- 🚪 不需要服务时
- 💻 内存不足时
- 🧹 清理环境

### 方式 3：手动管理

**启动服务**：
```bash
docker compose up -d
```

**查看状态**：
```bash
docker ps
```

**查看日志**：
```bash
docker logs -f rss-person-rsshub
docker logs -f rss-person-redis
```

**停止服务**：
```bash
docker compose down
```

## 内存对比

| 状态 | Docker 服务 | 内存占用 |
|------|------------|----------|
| **运行中** | RSSHub + Redis | ~285 MB |
| **已停止** | 无 | 0 MB |

## OrbStack 说明

**OrbStack** 已安装在系统上，但它**不能直接管理 macOS 原生 Docker**。

OrbStack 是用于在 macOS 上运行 **Linux 虚拟机** 的工具，不适合本项目。请使用上面介绍的快捷脚本或 Docker Desktop。

## 注意事项

1. **定时任务**
   - 配置文件：`com.aireport.daily.plist`
   - 运行时间：每天 7:00 AM
   - 使用脚本：`daily_report_with_docker_check.sh`（自动检查 Docker）

2. **数据持久化**
   - 停止容器**不会**删除数据
   - 重新启动时会恢复之前的状态

3. **查看日志**
   - 输出日志：`logs/stdout.log`
   - 错误日志：`logs/stderr.log`

## 常见问题

**Q: 容器启动失败？**
```bash
# 检查端口占用
lsof -i :1200

# 查看容器日志
docker logs rss-person-rsshub
```

**Q: 定时任务不运行？**
```bash
# 检查定时任务状态
./manage_cron.sh status

# 查看日志
tail -20 logs/stderr.log
```

**Q: 需要更多 RSS 源？**
- 新增了 27 个高质量 AI RSS 源（从 awesome-AI-feeds）
- 总源数：47 个
- 配置文件：`lib/rss_collector.py`
