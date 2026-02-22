# 云服务器部署指南（2核2G 优化版）

## 系统要求

- **配置**: 2核2G 云服务器
- **操作系统**: Ubuntu 20.04+ / CentOS 7+ / Debian 10+
- **预计内存占用**: ~600-800MB（相比 Docker 版本节省 ~400MB）

---

## 部署方案选择

### 方案 A：持续运行（推荐）

| 优点 | 缺点 |
|------|------|
| 响应快，RSSHub 随时可用 | 持续占用 ~350MB 内存 |
| 一天运行多次更高效 | - |
| 稳定可靠 | - |

**适合场景**：一天运行多次，或需要手动测试时

### 方案 B：按需启动（省内存）

| 优点 | 缺点 |
|------|------|
| 节省内存（仅运行时占用） | 每次启动多等待 10-20 秒 |
| 一天只运行一次时更优 | 频繁启停有额外开销 |

**适合场景**：每天固定时间运行一次

---

## 部署架构

```
┌─────────────────────────────────────────────────────┐
│                   云服务器 (2核2G)                   │
├─────────────────────────────────────────────────────┤
│  ┌──────────────┐      ┌──────────────┐             │
│  │ RSSHub (npm) │◄────►│  Redis       │             │
│  │  ~250MB      │      │  ~80MB       │             │
│  │  Port:1200   │      │  Port:6379   │             │
│  └──────────────┘      └──────────────┘             │
│                                                      │
│  ┌──────────────────────────────────────────────┐   │
│  │  Python 脚本 (定时运行)                       │   │
│  │  - RSS 采集                                   │   │
│  │  - AI 分析 (调用 DeepSeek API)                │   │
│  │  - 本地保存 JSON                              │   │
│  └──────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

---

## 一、基础环境安装

### 1.1 安装 Node.js 和 npm

```bash
# Ubuntu/Debian
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# CentOS/RHEL
curl -fsSL https://rpm.nodesource.com/setup_18.x | sudo bash -
sudo yum install -y nodejs

# 验证安装
node -v  # 应该显示 v18.x.x
npm -v   # 应该显示 9.x.x 或更高
```

### 1.2 安装 Python 3 和 pip

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y python3 python3-pip python3-venv

# CentOS/RHEL
sudo yum install -y python3 python3-pip

# 验证安装
python3 --version
pip3 --version
```

### 1.3 安装 Redis

```bash
# Ubuntu/Debian
sudo apt install -y redis-server

# CentOS/RHEL
sudo yum install -y redis

# 启动 Redis
sudo systemctl start redis
sudo systemctl enable redis

# 验证运行
redis-cli ping  # 应该返回 PONG
```

---

## 二、部署 RSSHub（npm 方式）

### 2.1 全局安装 RSSHub

```bash
# 使用 npm 全局安装（推荐）
npm install -g rsshub

# 或者使用 yarn（如果已安装）
# yarn global add rsshub
```

### 2.2 创建 RSSHub 配置文件

```bash
# 创建配置目录
mkdir -p ~/.rsshub
cd ~/.rsshub
```

创建配置文件 `config.json`：

```json
{
  "PORT": 1200,
  "NODE_ENV": "production",
  "CACHE_TYPE": "redis",
  "REDIS_URL": "redis://127.0.0.1:6379",
  "CACHE_EXPIRE": 300,
  "CACHE_CONTENT_EXPIRE": 600,
  "TWITTER_AUTH_TOKEN": "你的twitter_auth_token"
}
```

### 2.3 选择运行模式

#### 模式 A：使用 PM2 持续运行（推荐）

```bash
# 全局安装 PM2
npm install -g pm2

# 启动 RSSHub
pm2 start rsshub --name "rss-person-rsshub" -- --config ~/.rsshub/config.json

# 设置开机自启
pm2 startup
pm2 save

# 查看运行状态
pm2 status
pm2 logs rss-person-rsshub

# 内存优化配置
pm2 install pm2-logrotate
pm2 set pm2-logrotate:max_size 10M
pm2 set pm2-logrotate:retain 7
```

#### 模式 B：按需启动（省内存方案）

创建启动脚本 `~/start-services.sh`：

```bash
#!/bin/bash

# 启动 Redis
echo "🚀 启动 Redis..."
sudo systemctl start redis
sleep 2

# 等待 Redis 就绪
until redis-cli ping > /dev/null 2>&1; do
    echo "⏳ 等待 Redis 启动..."
    sleep 1
done
echo "✅ Redis 已就绪"

# 启动 RSSHub
echo "🚀 启动 RSSHub..."
nohup rsshub --config ~/.rsshub/config.json > ~/.rsshub/rsshub.log 2>&1 &
RSSHUB_PID=$!
echo $RSSHUB_PID > ~/.rsshub/rsshub.pid

# 等待 RSSHub 就绪
echo "⏳ 等待 RSSHub 启动..."
for i in {1..30}; do
    if curl -s http://localhost:1200 > /dev/null 2>&1; then
        echo "✅ RSSHub 已就绪"
        break
    fi
    sleep 1
done

echo "✅ 所有服务已启动"
```

创建停止脚本 `~/stop-services.sh`：

```bash
#!/bin/bash

echo "🛑 停止 RSSHub..."
if [ -f ~/.rsshub/rsshub.pid ]; then
    RSSHUB_PID=$(cat ~/.rsshub/rsshub.pid)
    kill $RSSHUB_PID 2>/dev/null
    rm ~/.rsshub/rsshub.pid
    echo "✅ RSSHub 已停止"
fi

echo "🛑 停止 Redis..."
sudo systemctl stop redis
echo "✅ 所有服务已停止"
```

设置执行权限：

```bash
chmod +x ~/start-services.sh
chmod +x ~/stop-services.sh
```

### 2.4 验证 RSSHub 运行

```bash
# 测试本地访问
curl http://localhost:1200/twitter/user/OpenAI

# 查看日志（按需启动模式）
tail -f ~/.rsshub/rsshub.log

# 查看状态（PM2 模式）
pm2 status
```

---

## 三、部署 Python 项目

### 3.1 克隆项目

```bash
# 创建项目目录
mkdir -p ~/projects
cd ~/projects

# 克隆项目（替换为你的仓库地址）
git clone https://github.com/yourusername/ai-RSS-person.git
cd ai-RSS-person
```

### 3.2 安装 Python 依赖

```bash
# 创建虚拟环境（推荐）
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 3.3 配置环境变量

```bash
# 复制配置文件模板
cp .env.example .env

# 编辑配置
vim .env
```

**必需配置**：

```bash
# DeepSeek API
DEEPSEEK_API_KEY=sk-xxxxx

# RSSHub 地址（本地部署）
RSSHUB_HOST=http://127.0.0.1:1200

# 可选：代理配置（如果需要）
# PROXY_URL=http://127.0.0.1:7890
```

### 3.4 测试运行

```bash
# 激活虚拟环境
source ~/projects/ai-RSS-person/venv/bin/activate

# 运行测试
cd ~/projects/ai-RSS-person
python3 daily_report_PRO_cloud.py
```

---

## 四、配置定时任务

### 4.1 模式 A：持续运行版本（PM2）

创建 systemd 定时器 `/etc/systemd/system/ai-daily-report.service`：

```ini
[Unit]
Description=AI Daily Report Generator
After=network.target

[Service]
Type=oneshot
User=root
WorkingDirectory=/root/projects/ai-RSS-person
Environment="PATH=/root/projects/ai-RSS-person/venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/root/projects/ai-RSS-person/venv/bin/python /root/projects/ai-RSS-person/daily_report_PRO_cloud.py
StandardOutput=append:/var/log/ai-daily-report.log
StandardError=append:/var/log/ai-daily-report.error.log

[Install]
WantedBy=multi-user.target
```

创建定时器 `/etc/systemd/system/ai-daily-report.timer`：

```ini
[Unit]
Description=AI Daily Report Timer
Requires=ai-daily-report.service

[Timer]
OnCalendar=daily
OnCalendar=09:00
Persistent=true

[Install]
WantedBy=timers.target
```

启用定时器：

```bash
sudo systemctl daemon-reload
sudo systemctl start ai-daily-report.timer
sudo systemctl enable ai-daily-report.timer
```

### 4.2 模式 B：按需启动版本

创建包装脚本 `/root/run-daily-report.sh`：

```bash
#!/bin/bash

set -e

LOG_FILE="/var/log/ai-daily-report.log"
PROJECT_DIR="/root/projects/ai-RSS-person"

echo "========================================" >> $LOG_FILE
echo "$(date '+%Y-%m-%d %H:%M:%S') - 开始运行" >> $LOG_FILE

# 1. 启动服务
echo "$(date '+%Y-%m-%d %H:%M:%S') - 启动 RSSHub 和 Redis..." >> $LOG_FILE
bash ~/start-services.sh >> $LOG_FILE 2>&1

# 等待服务就绪
sleep 5

# 2. 运行 Python 脚本
echo "$(date '+%Y-%m-%d %H:%M:%S') - 运行日报生成..." >> $LOG_FILE
cd $PROJECT_DIR
source venv/bin/activate
python3 daily_report_PRO_cloud.py >> $LOG_FILE 2>&1

# 3. 停止服务
echo "$(date '+%Y-%m-%d %H:%M:%S') - 停止服务..." >> $LOG_FILE
bash ~/stop-services.sh >> $LOG_FILE 2>&1

echo "$(date '+%Y-%m-%d %H:%M:%S') - 运行完成" >> $LOG_FILE
echo "========================================" >> $LOG_FILE
```

设置权限：

```bash
chmod +x /root/run-daily-report.sh
```

配置 crontab：

```bash
crontab -e

# 每天早上 9:00 运行
0 9 * * * /root/run-daily-report.sh
```

或者使用 systemd：

```ini
# /etc/systemd/system/ai-daily-report.service
[Unit]
Description=AI Daily Report Generator (On-demand)
After=network.target

[Service]
Type=oneshot
User=root
ExecStart=/root/run-daily-report.sh
StandardOutput=append:/var/log/ai-daily-report.log
StandardError=append:/var/log/ai-daily-report.error.log

[Install]
WantedBy=multi-user.target
```

---

## 五、内存优化建议

### 5.1 Redis 内存优化

编辑 `/etc/redis/redis.conf`：

```bash
# 最大内存限制 100MB
maxmemory 100mb

# 内存淘汰策略（LRU）
maxmemory-policy allkeys-lru
```

重启 Redis：

```bash
sudo systemctl restart redis
```

### 5.2 RSSHub 内存优化

**PM2 模式**：

```bash
# 限制内存 300MB
pm2 stop rss-person-rsshub
pm2 start rsshub --name "rss-person-rsshub" --max-memory-restart 300M -- --config ~/.rsshub/config.json
pm2 save
```

**按需启动模式**：无需额外配置，运行完自动释放

### 5.3 创建 swap（防止 OOM）

```bash
# 创建 1GB swap 文件
sudo fallocate -l 1G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# 永久生效
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# 调整 swappiness（优先使用物理内存）
sudo sysctl vm.swappiness=10
echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf
```

### 5.4 监控内存使用

```bash
# 实时监控
watch -n 2 free -h

# 查看进程内存占用
ps aux --sort=-%mem | head -20

# PM2 监控
pm2 monit
```

---

## 六、资源占用对比

### 模式 A：持续运行

| 组件 | 内存占用 | 说明 |
|------|----------|------|
| RSSHub (npm) | ~250-300MB | 持续运行 |
| Redis | ~80-100MB | 持续运行 |
| Python 脚本 | ~50-100MB | 仅运行时 |
| 系统开销 | ~200-300MB | OS + 其他 |
| **总计** | **~700-800MB** | 剩余 ~1.2GB |

### 模式 B：按需启动

| 状态 | 内存占用 | 说明 |
|------|----------|------|
| 空闲时 | ~200-300MB | 仅系统 + 其他项目 |
| 运行时 | ~700-800MB | RSSHub + Redis + Python |
| **平均** | **~300-400MB** | 大部分时间空闲 |

**节省内存**：约 400MB 持续占用

---

## 七、故障排查

### 7.1 RSSHub 无法启动

```bash
# 查看日志
pm2 logs rss-person-rsshub --lines 100  # PM2 模式
tail -f ~/.rsshub/rsshub.log           # 按需模式

# 检查端口占用
sudo netstat -tlnp | grep 1200

# 检查 Redis 连接
redis-cli ping
```

### 7.2 服务启动失败

```bash
# 测试配置文件
rsshub --config ~/.rsshub/config.json --help

# 手动启动查看错误
rsshub --config ~/.rsshub/config.json
```

### 7.3 内存不足

```bash
# 检查内存使用
free -h

# 查看 OOM 日志
sudo dmesg | grep -i "out of memory"

# 重启服务
pm2 restart rss-person-rsshub
sudo systemctl restart redis
```

---

## 八、更新与维护

### 更新 RSSHub

```bash
# 更新全局包
npm update -g rsshub

# 重启服务（PM2 模式）
pm2 restart rss-person-rsshub

# 按需模式无需更新操作
```

### 更新项目代码

```bash
cd ~/projects/ai-RSS-person
git pull
source venv/bin/activate
pip install -r requirements.txt --upgrade
```

---

## 九、卸载方案

```bash
# PM2 模式卸载
pm2 delete rss-person-rsshub
pm2 uninstall pm2-logrotate

# 按需模式卸载（删除启动脚本）
rm -f ~/start-services.sh ~/stop-services.sh

# 停止定时器
sudo systemctl stop ai-daily-report.timer
sudo systemctl disable ai-daily-report.timer
sudo rm /etc/systemd/system/ai-daily-report.*

# 卸载软件
npm uninstall -g rsshub pm2
sudo apt remove redis-server -y  # Ubuntu/Debian

# 删除项目
rm -rf ~/projects/ai-RSS-person
rm -rf ~/.rsshub
```

---

## 十、方案选择建议

### 选择持续运行（PM2）如果：
- ✅ 一天需要运行多次
- ✅ 需要手动测试或调试
- ✅ 服务器内存充足（>1GB 剩余）

### 选择按需启动如果：
- ✅ 每天固定时间运行一次
- ✅ 内存紧张（<1GB 剩余）
- ✅ 不需要频繁测试

---

## 相关文档

- [云上传配置指南](CLOUD_UPLOAD_GUIDE.md)
- [macOS 定时任务](MAC_CRON_GUIDE.md)
- [完整使用指南](../README.md)
