# RSS-person - AI资讯自动生成与发布工具

**AI驱动的单用户RSS聚合和报告生成系统**

自动采集全球AI资讯，通过 DeepSeek AI 智能分析，生成专业日报并自动上传到云服务器。

---

## ✨ 核心特性

- ✅ **智能排序**: 双维度评分系统（来源权威性60% + 内容相关性40%）
- ✅ **成本优化**: 智能筛选，节省87% API费用
- ✅ **自动上传**: 支持自动上传到云服务器（SFTP/HTTP/FTP）
- ✅ **Mac定时任务**: 每天早上9:00自动运行（使用launchd）
- ✅ **58个优质RSS源**: Twitter、科技博客、微信公众号、学术期刊
- ✅ **完整报告**: 包含导读、AI分析、原文链接、结语

---

## 📋 项目架构

```
RSS 数据源 (58个)
├── Twitter/X → RSSHub (localhost:1200)
├── 科技博客 → 直连/代理/cffi
├── 微信公众号 → wewe-rss (localhost:4000)
└── 中文RSS → RSSHub
         ↓
daily_report_PRO_cloud.py
  ├─ RSS采集
  ├─ 智能排序
  ├─ AI分析（DeepSeek）
  ├─ 本地保存（reports/）
  └─ 自动上传（8.135.37.159）
```

---

## 🚀 快速开始

### 1. 环境准备

**必需软件：**
- Python 3.8+
- Docker & Docker Compose
- DeepSeek API Key ([获取地址](https://platform.deepseek.com/))

**安装依赖：**
```bash
# Python依赖
pip install -r requirements.txt

# 或单独安装
pip install feedparser requests openai python-dotenv paramiko curl-cffi
```

### 2. 配置环境变量

```bash
# 复制配置模板
cp .env.example .env

# 编辑配置文件
vim .env  # 或使用任何文本编辑器
```

**必需配置项：**
```bash
# DeepSeek API（必填）
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxx

# 代理配置（如果需要）
PROXY_URL=http://127.0.0.1:7897

# RSSHub地址
RSSHUB_HOST=http://localhost:1200

# 云服务器配置（自动上传）
CLOUD_SERVER_HOST=8.135.37.159
CLOUD_SERVER_PORT=22
CLOUD_SERVER_USER=root
CLOUD_SERVER_KEY_PATH=/Users/MarkHuang/.ssh/id_rsa
CLOUD_SERVER_REMOTE_PATH=/var/www/html/reports
UPLOAD_METHOD=sftp
```

### 3. 启动Docker服务

```bash
# 启动所有必需服务（RSSHub、Redis、wewe-rss、MySQL）
docker compose up -d

# 检查服务状态
docker ps
```

**服务说明：**
- `rss-person-rsshub` (端口1200): Twitter和中文RSS源
- `rss-person-wewe-rss` (端口4000): 微信公众号源
- `rss-person-redis`: RSSHub缓存
- `rss-person-mysql`: wewe-rss数据库

### 4. 手动测试运行

```bash
# 运行一次完整流程
python3 daily_report_PRO_cloud.py
```

**预期结果：**
1. ✅ 采集过去24小时的RSS资讯
2. ✅ AI分析并生成HTML报告
3. ✅ 保存到 `reports/` 目录
4. ✅ 自动上传到云服务器
5. ✅ 显示访问地址

---

## ⏰ 设置Mac定时任务（每天自动运行）

### 安装定时任务

```bash
# 一键安装
./manage_cron.sh install
```

**这会：**
- ✅ 设置每天早上 9:00 自动运行
- ✅ 自动保存日志到 `logs/` 目录
- ✅ 即使Mac休眠也会在唤醒后执行

### 定时任务管理命令

```bash
./manage_cron.sh install     # 安装定时任务
./manage_cron.sh uninstall   # 卸载定时任务
./manage_cron.sh status      # 查看任务状态
./manage_cron.sh logs        # 查看运行日志
./manage_cron.sh test        # 手动运行一次
./manage_cron.sh edit        # 编辑运行时间
```

### 修改运行时间

默认：每天早上 9:00

修改方法：
```bash
./manage_cron.sh edit
```

找到这一行并修改：
```xml
<key>Hour</key>
<integer>9</integer>    <!-- 修改为想要的小时（0-23） -->
<key>Minute</key>
<integer>0</integer>    <!-- 修改为想要的分钟（0-59） -->
```

修改后重新安装：
```bash
./manage_cron.sh uninstall
./manage_cron.sh install
```

### Mac系统设置建议

**防止Mac自动休眠：**
```
系统设置 → 电池 → 选项 → 防止自动睡眠
```

**设置定时唤醒（推荐）：**
```
系统设置 → 电池 → 计划
设置每天早上 8:55 自动唤醒（留5分钟缓冲）
```

---

## 📊 查看结果

### 本地报告

```bash
# 查看生成的报告
ls -lh reports/

# 打开最新报告
open reports/$(ls -t reports/*.html | head -1)
```

### 云服务器报告

**访问地址：**
```
http://8.135.37.159/reports/
```

**查看最新报告：**
```bash
# SSH登录服务器
ssh root@8.135.37.159

# 查看报告文件
ls -lh /var/www/html/reports/
```

### 查看日志

```bash
# 查看定时任务日志
./manage_cron.sh logs

# 查看完整日志文件
cat logs/stdout.log
cat logs/stderr.log

# 查看最近50行
tail -50 logs/stdout.log
```

---

## 📁 项目文件说明

### 核心程序

| 文件 | 说明 | 用途 |
|------|------|------|
| `daily_report_PRO_cloud.py` | 云服务器版本（主要使用） | 采集+AI+上传到服务器 |
| `daily_report_PRO_server.py` | 服务器本地版本 | 以后迁移到服务器使用 |
| `daily_report_PRO_wechat.py` | 微信版 | 发布到微信公众号草稿 |
| `article_ranker.py` | 文章排序器 | 智能排序评分 |
| `rss_collector.py` | RSS验证工具 | 测试RSS源是否可用 |
| `wechat_publisher.py` | 微信发布模块 | 微信公众号发布 |

### 配置文件

| 文件 | 说明 |
|------|------|
| `.env` | 环境变量配置（API密钥、代理等） |
| `.env.example` | 配置模板 |
| `docker-compose.yml` | Docker服务配置 |
| `requirements.txt` | Python依赖列表 |

### 定时任务

| 文件 | 说明 |
|------|------|
| `com.aireport.daily.plist` | Mac定时任务配置（launchd） |
| `manage_cron.sh` | 定时任务管理脚本 |
| `MAC_CRON_GUIDE.md` | 定时任务详细指南 |

### 测试工具

| 文件 | 说明 |
|------|------|
| `test_upload.py` | SFTP上传测试 |
| `verify.py` | 项目配置验证 |

### 文档

| 文件 | 说明 |
|------|------|
| `README.md` | 本文档 |
| `CLOUD_UPLOAD_GUIDE.md` | 云服务器配置指南 |

---

## 🔧 常用命令

### Docker管理

```bash
# 启动服务
docker compose up -d

# 查看运行状态
docker ps

# 查看日志
docker logs rss-person-rsshub --tail 50

# 重启服务
docker compose restart

# 停止服务
docker compose down
```

### RSS验证

```bash
# 验证RSS源是否可用
python3 rss_collector.py
```

### 手动运行

```bash
# 运行云服务器版本（推荐）
python3 daily_report_PRO_cloud.py

# 运行微信版本
python3 daily_report_PRO_wechat.py
```

---

## 💰 成本说明

### DeepSeek API定价

| 类型 | 价格 | 说明 |
|------|------|------|
| 输入 | ¥2/百万tokens | Cache Hit: ¥0.2/百万 |
| 输出 | ¥3/百万tokens | - |

### 实际消耗

- 每次运行约：50,000-100,000 tokens
- 费用约：¥0.15-0.30/次
- 每天运行1次，月费用约：**¥5-10**

---

## ⚠️ 常见问题

### 问题1：RSS源采集失败

**检查Docker服务：**
```bash
docker ps | grep rsshub
curl http://localhost:1200/twitter/user/OpenAI
```

**解决方法：**
- 重启RSSHub：`docker compose restart rsshub`
- RSSHub刚启动需要等待缓存建立（约5-10分钟）

### 问题2：定时任务没有运行

**检查：**
```bash
./manage_cron.sh status
./manage_cron.sh logs
```

**常见原因：**
- Mac在定时时间处于休眠状态
- Python路径不正确
- .env文件配置错误

### 问题3：上传到服务器失败

**测试SSH连接：**
```bash
ssh root@8.135.37.159
```

**测试SFTP上传：**
```bash
python3 test_upload.py
```

### 问题4：AI分析失败

**检查：**
- DeepSeek API Key是否正确
- API余额是否充足
- 网络连接是否正常

---

## 📈 下一步计划

### 一个月后的选择

**选项1：继续使用Mac**
- ✅ 简单，已配置好
- ⚠️ 需要保持Mac开机

**选项2：迁移到云服务器**
- ✅ 24/7运行，更可靠
- ✅ 代码已准备好（`daily_report_PRO_server.py`）
- ✅ 只需在服务器上设置crontab即可

**迁移到服务器的步骤：**
1. 在服务器上安装相同的环境
2. 上传代码和配置文件
3. 设置crontab定时任务
4. 测试运行

---

## 📞 获取帮助

### 查看详细文档

- `MAC_CRON_GUIDE.md` - Mac定时任务完整指南
- `CLOUD_UPLOAD_GUIDE.md` - 云服务器配置详解
- `PROJECT_COMPARISON.md` - 项目版本对比

### 验证项目配置

```bash
# 运行验证脚本
python3 verify.py
```

---

## 📄 License

MIT

---

## 🎉 现在就可以开始！

```bash
# 1. 配置环境变量
vim .env

# 2. 启动Docker服务
docker compose up -d

# 3. 测试运行一次
python3 daily_report_PRO_cloud.py

# 4. 安装定时任务
./manage_cron.sh install

# 5. 等待明天早上9:00自动运行！✨
```

**享受自动化带来的便利！** 🚀
