# 从不会部署到成功上线：Codex 实战记录

本文记录一次真实上线过程：用户不会部署 Linux 服务，通过 Codex 远程排障并最终跑通「定时日报 + 本地复制 + 邮件 + Twitter Cookie 轮换」全链路。

## 1. 目标与最终状态

目标：
- 在服务器上每天自动生成 AI 日报
- 生成后复制到 `/var/www/json/report`
- 邮件自动发送
- 每周自动轮换 Twitter Cookie

最终已达成：
- `ai-rss-daily.timer`：北京时间每天早上 07:00 左右执行
- `ai-rss-cleanup.timer`：定时清理历史产物
- `ai-rss-cookie-rotate.timer`：每周执行 Cookie 轮换
- `RSSHub` 已以 `pm2` 方式运行在 `http://localhost:1200`
- 主流程一次手动触发验证成功（日报生成 + 复制 + 邮件发送）

## 2. 实际踩坑与修复过程

### 坑 1：登录错服务器，目录结构不对

现象：
- `cd /opt` 报错目录不存在

原因：
- 登录到了另一台机器，不是目标服务器

修复：
- 切换到正确机器后继续部署，统一使用 `/opt/ai-RSS-person`

---

### 坑 2：timer 不存在（`Unit file ... does not exist`）

现象：
- `systemctl enable ai-rss-daily.timer` 报找不到 unit

原因：
- 项目里的 `*.service/*.timer` 还没复制到 `/etc/systemd/system/`

修复命令：
```bash
cp /opt/ai-RSS-person/scripts/server/ai-rss-daily.service /etc/systemd/system/
cp /opt/ai-RSS-person/scripts/server/ai-rss-daily.timer /etc/systemd/system/
cp /opt/ai-RSS-person/scripts/server/ai-rss-cleanup.service /etc/systemd/system/
cp /opt/ai-RSS-person/scripts/server/ai-rss-cleanup.timer /etc/systemd/system/
cp /opt/ai-RSS-person/scripts/server/ai-rss-cookie-rotate.service /etc/systemd/system/
cp /opt/ai-RSS-person/scripts/server/ai-rss-cookie-rotate.timer /etc/systemd/system/
chmod 644 /etc/systemd/system/ai-rss-*
systemctl daemon-reload
systemctl enable --now ai-rss-daily.timer
systemctl enable --now ai-rss-cleanup.timer
systemctl enable --now ai-rss-cookie-rotate.timer
```

---

### 坑 3：Python 虚拟环境不存在（`status=203/EXEC`）

现象：
- 服务启动失败：`Failed to locate executable /opt/ai-RSS-person/.venv/bin/python`

原因：
- 没创建 `.venv`，系统找不到运行解释器

修复命令：
```bash
cd /opt/ai-RSS-person
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip setuptools wheel
.venv/bin/pip install -r requirements.lock.txt
```

---

### 坑 4：依赖缺失（`No module named 'yaml'`）

现象：
- 前台运行 `daily_report_PRO_cloud.py` 报 `ModuleNotFoundError: No module named 'yaml'`

原因：
- 服务器环境缺少 `PyYAML`

修复命令：
```bash
cd /opt/ai-RSS-person
.venv/bin/pip install PyYAML
```

---

### 坑 5：RSSHub 未运行，RSSHub 路由源全部失败

现象：
- 采集日志中 `localhost:1200` 连接被拒绝
- `36氪/量子位/InfoQ` 等 RSSHub 路由报错

原因：
- 服务器上没有可用的 RSSHub 进程

修复策略（方案 A）：
- 在服务器部署 RSSHub（独立目录 `/opt/rsshub`）
- 使用 `pm2` 常驻
- 项目 `.env` 指向 `RSSHUB_HOST=http://localhost:1200`

关键命令（实战版）：
```bash
cd /opt
git clone --depth 1 https://github.com/DIYgod/RSSHub.git /opt/rsshub
cd /opt/rsshub
pnpm config set registry https://registry.npmjs.org
npm config set registry https://registry.npmjs.org
pnpm install
pnpm run build
cat > .env <<EOF
PORT=1200
NODE_ENV=production
EOF
pm2 start "pnpm start" --name rsshub --cwd /opt/rsshub
pm2 save
pm2 startup systemd -u root --hp /root
curl -I http://localhost:1200
```

项目 `.env` 同步：
```env
RSSHUB_HOST=http://localhost:1200
RSSHUB_PM2_NAME=rsshub
RSSHUB_SERVICE_NAME=
RSSHUB_RESTART_CMD=
```

## 3. 生产 `.env` 核心配置（本次模式）

至少确保：
```env
DEEPSEEK_API_KEY=...
UPLOAD_ENABLED=false
LOCAL_TARGET_DIR=/var/www/json/report
EMAIL_ENABLED=true
SMTP_SERVER=...
SMTP_PORT=...
SENDER_EMAIL=...
SENDER_PASSWORD=...
RECEIVER_EMAIL=...
TWITTER_AUTH_TOKEN=...
TWITTER_CT0=...
TWITTER_COOKIE_SOURCE_FILE=/opt/ai-RSS-person/secrets/twitter_cookie.txt
RSSHUB_HOST=http://localhost:1200
RSSHUB_PM2_NAME=rsshub
```

## 4. 关键验证命令（上线后必须跑）

### 4.1 定时器状态
```bash
systemctl status ai-rss-daily.timer --no-pager
systemctl status ai-rss-cleanup.timer --no-pager
systemctl status ai-rss-cookie-rotate.timer --no-pager
systemctl list-timers | grep ai-rss
```

### 4.2 主流程手动触发
```bash
systemctl start ai-rss-daily.service
journalctl -u ai-rss-daily.service -n 200 --no-pager
```

成功信号：
- `已复制报告到目标目录: /var/www/json/report/YYYY-MM-DD.json`
- `邮件发送成功`
- 服务退出码 `status=0/SUCCESS`

### 4.3 Cookie 轮换链路
```bash
systemctl start ai-rss-cookie-rotate.service
journalctl -u ai-rss-cookie-rotate.service -n 200 --no-pager
```

### 4.4 RSSHub 存活
```bash
pm2 list
curl -I http://localhost:1200
```

## 5. 调整定时到早上 7 点（已执行）

当前配置为：
```ini
OnCalendar=07:00
TimeZone=Asia/Shanghai
RandomizedDelaySec=5min
```

因此实际触发一般在北京时间 `07:00~07:05`。

## 6. Git 远程推送能力（服务器侧）

已完成：
- 配置 `git config --global user.name "Mark"`
- 配置 `git config --global user.email "1415994589@qq.com"`
- 生成专用 SSH key（服务器）
- 远端从 HTTPS 改为 SSH（`git@github-mark:...`）
- 验证通过：`ssh -T git@github-mark` 成功认证

## 7. 最终结论

即使不会 Linux 部署，也可以按「日志驱动 + 逐步收敛」完成上线：
- 先让服务能启动（解释器、依赖）
- 再让外部依赖可用（RSSHub）
- 再收敛业务链路（生成、复制、邮件、轮换）
- 最后固化为定时任务和可复用命令

这个流程可以直接复用到下一台服务器。
