# RSSHub 部署迁移指南

## 从 Docker 迁移到 npm 部署

### 本地 Mac 部署

#### 1. npm 部署已完成
- 位置: `~/rsshub-service/`
- 启动命令: `cd ~/rsshub-service && npm start dist/index.mjs`
- 后台启动: `nohup npm start dist/index.mjs > logs/startup.log 2>&1 &`

#### 2. 配置文件位置
- 环境变量: `~/rsshub-service/.env`
- 日志目录: `~/rsshub-service/logs/`

#### 3. 管理命令
```bash
# 启动
cd ~/rsshub-service && npm start dist/index.mjs &

# 停止
kill $(ps aux | grep "node.*dist/index.mjs" | grep -v grep | awk '{print $1}')

# 查看日志
tail -f ~/rsshub-service/logs/startup.log

# 测试
curl "http://localhost:1200/twitter/user/OpenAI"
```

---

## 服务器部署 (Ubuntu/Debian)

### 自动部署脚本

将 `deploy-rsshub-server.sh` 上传到服务器后运行:

```bash
# 上传脚本到服务器
scp deploy-rsshub-server.sh root@your-server:/root/

# SSH 登录服务器
ssh root@your-server

# 运行部署脚本
chmod +x deploy-rsshub-server.sh
sudo ./deploy-rsshub-server.sh
```

### 手动部署步骤

#### 1. 安装 Node.js
```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt-get install -y nodejs
```

#### 2. 克隆并构建 RSSHub
```bash
cd /opt
git clone https://github.com/DIYgod/RSSHub.git
cd RSSHub
npm install --legacy-peer-deps
npm run build
```

#### 3. 配置环境变量
```bash
cat > .env << 'EOF'
NODE_ENV=production
PORT=1200
CACHE_TYPE=memory
CACHE_EXPIRE=600
CACHE_CONTENT_EXPIRE=3600
TWITTER_AUTH_TOKEN=你的token
TWITTER_CT0=你的ct0
LOGGER_LEVEL=info
REQUEST_TIMEOUT=30000
EOF
```

#### 4. 创建 systemd 服务
```bash
cat > /etc/systemd/system/rsshub.service << 'EOF'
[Unit]
Description=RSSHub Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/RSSHub
EnvironmentFile=/opt/RSSHub/.env
ExecStart=/usr/bin/node /opt/RSSHub/dist/index.mjs
Restart=always
StandardOutput=append:/opt/RSSHub/logs/rsshub.log
StandardError=append:/opt/RSSHub/logs/rsshub-error.log

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable rsshub
systemctl start rsshub
```

---

## 资源对比

| 部署方式 | 内存占用 | 优点 | 缺点 |
|---------|---------|------|------|
| Docker | ~400MB | 简单，隔离性好 | 占用内存高 |
| npm (无 Redis) | ~150-200MB | 省内存 | 配置稍复杂 |

---

## 配置迁移对照表

| Docker 配置 | npm 配置 (.env) |
|------------|-----------------|
| `environment:` | 写入 `.env` 文件 |
| `-e CACHE_TYPE=redis` | `CACHE_TYPE=memory` (省内存) |
| `-e TWITTER_AUTH_TOKEN=xxx` | `TWITTER_AUTH_TOKEN=xxx` |
| `-e PROXY_URI=xxx` | `PROXY_URI=xxx` |
| `ports: -1200:1200` | `PORT=1200` |

---

## 常用命令

### Mac 本地
```bash
# 启动
cd ~/rsshub-service && npm start dist/index.mjs &

# 停止
pkill -f "node.*dist/index.mjs"

# 重启
pkill -f "node.*dist/index.mjs" && cd ~/rsshub-service && npm start dist/index.mjs &
```

### 服务器
```bash
# 启动
systemctl start rsshub

# 停止
systemctl stop rsshub

# 重启
systemctl restart rsshub

# 状态
systemctl status rsshub

# 日志
tail -f /opt/RSSHub/logs/rsshub.log
```

---

## 测试验证

```bash
# 测试 Twitter 源
curl "http://localhost:1200/twitter/user/OpenAI"

# 测试中文源
curl "http://localhost:1200/36kr/information/AI"
```
