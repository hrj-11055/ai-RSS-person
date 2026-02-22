# RSS-Person 项目文件交互关系图

## 📊 整体架构流程图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         RSS-Person 项目系统                              │
└─────────────────────────────────────────────────────────────────────────┘

┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  macOS 定时   │────▶│ manage_cron  │────▶│  launchd     │
│   任务调度    │     │    .sh       │     │    .plist    │
└──────────────┘     └──────────────┘     └──────────────┘
       │                                          │
       │         (每天 9:00 自动执行)              │
       └──────────────────┬───────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      主程序入口 (三选一)                                  │
├─────────────────────────────────────────────────────────────────────────┤
│  📱 daily_report_PRO_cloud.py  ⭐ (推荐 - 云服务器版)                      │
│  📱 daily_report_PRO_server.py      (服务器本地版 - 未来用)               │
│  📱 daily_report_PRO_wechat.py      (微信公众号版)                       │
└─────────────────────────────────────────────────────────────────────────┘
                          │
                          │ 导入使用
                          ▼
        ┌─────────────────┴─────────────────┐
        │                                     │
        ▼                                     ▼
┌──────────────────┐              ┌──────────────────┐
│ article_ranker   │              │  RSS 数据采集     │
│     .py          │              │  (内置函数)       │
│  文章智能排序     │              │  58个RSS源        │
└──────────────────┘              └──────────────────┘
        │                                     │
        │                                     ▼
        │                        ┌──────────────────────┐
        │                        │   Docker 服务依赖     │
        │                        ├──────────────────────┤
        │                        │ 🐳 RSSHub (1200)     │
        │                        │ 📦 Redis (缓存)       │
        │                        │ 🐘 MySQL (可选)       │
        │                        │ 📰 wewe-rss (4000)   │
        │                        └──────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│                  报告生成流程                                 │
├─────────────────────────────────────────────────────────────┤
│  1. RSS 采集 → 58个源 (Twitter/博客/微信/学术)              │
│  2. 智能排序 → article_ranker.py (评分 0-100)               │
│  3. AI 分析 → DeepSeek API (生成摘要和见解)                  │
│  4. 生成报告 → HTML 格式 (带样式和响应式设计)                │
└─────────────────────────────────────────────────────────────┘
        │
        │ 保存本地
        ▼
┌──────────────────┐
│  reports/        │
│  AI_Daily_*.html │
└──────────────────┘
        │
        ├───┬──────────────┬──────────────┐
        │   │              │              │
        ▼   ▼              ▼              ▼
   ┌────────┐      ┌──────────┐    ┌──────────┐
   │ 云服务器 │      │ 微信版   │    │ 网站集成 │
   │  SFTP   │      │  草稿    │    │ SQLite  │
   │  上传   │      │          │    │         │
   └────────┘      └──────────┘    └──────────┘
   (cloud版)       (wechat版)     (可选)


## 📁 详细文件依赖关系

### 核心主程序依赖

```
daily_report_PRO_cloud.py
├── article_ranker.py ──────┐
│   └── ArticleRanker类     │ (评分系统)
├── openai (DeepSeek API)   │
├── feedparser              │
├── requests                │
├── paramiko                │ (SFTP上传)
└── .env ──────────────────┘ (配置文件)

daily_report_PRO_wechat.py
├── article_ranker.py ──────┐
├── wechat_publisher.py ────┼─ WeChatClient
│   └── 微信公众号发布       │
├── openai (DeepSeek API)   │
├── feedparser              │
├── requests                │
└── .env ──────────────────┘ (配置文件)

daily_report_PRO_server.py
├── article_ranker.py
├── openai
├── feedparser
└── .env
```

### 工具脚本

```
rss_collector.py (RSS源验证工具)
├── feedparser
├── requests
├── curl_cffi (反爬虫)
└── RSSHub服务

wechat_publisher.py (微信发布模块)
└── wechatpy

integrate_to_website.py (网站集成脚本)
└── sqlite3 (RSS-Spider数据库)
```

### 配置和管理文件

```
.env
├── DEEPSEEK_API_KEY
├── PROXY_URL
├── RSSHUB_HOST
├── CLOUD_SERVER_*
└── UPLOAD_METHOD

docker-compose.yml
├── rsshub服务
├── redis服务
├── mysql服务
└── wewe-rss服务

manage_cron.sh
└── com.aireport.daily.plist

test_upload.py (SFTP测试)
verify.py (配置验证)
```

## 🔄 数据流向

```
1. 定时触发
   launchd → manage_cron.sh → daily_report_PRO_*.py

2. 配置加载
   .env → 主程序 (API密钥/代理/服务器配置)

3. 数据采集
   RSS源 (58个) → RSS采集器 → 原始文章列表

4. 数据处理
   原始文章 → article_ranker.py → 排序后文章

5. AI分析
   排序后文章 → DeepSeek API → AI分析结果

6. 报告生成
   AI分析结果 → HTML生成 → reports/AI_Daily_*.html

7. 输出分发
   reports/*.html ─┬─→ 本地保存
                   ├─→ SFTP上传 (cloud版)
                   ├─→ 微信草稿 (wechat版)
                   └─→ 网站数据库 (integrate_to_website.py)
```

## 🎯 各版本功能对比

| 功能 | cloud版 | server版 | wechat版 |
|-----|---------|----------|---------|
| RSS采集 | ✅ | ✅ | ✅ |
| 智能排序 | ✅ | ✅ | ✅ |
| AI分析 | ✅ | ✅ | ✅ |
| HTML报告 | ✅ | ✅ | ✅ |
| 本地保存 | ✅ | ✅ | ✅ |
| SFTP上传 | ✅ | ❌ | ❌ |
| 微信发布 | ❌ | ❌ | ✅ |
| 定时任务 | ✅ | ✅ | ✅ |

## 📦 外部依赖服务

```
┌──────────────────────────────────────────────────┐
│              外部服务依赖                          │
├──────────────────────────────────────────────────┤
│  🤖 DeepSeek API (https://api.deepseek.com)      │
│     └─ AI分析和报告生成                           │
│                                                  │
│  🐳 Docker Compose Services                      │
│     ├─ RSSHub (localhost:1200)                  │
│     │  └─ Twitter/中文RSS源                      │
│     ├─ Redis (缓存)                              │
│     ├─ MySQL (wewe-rss数据库)                   │
│     └─ wewe-rss (localhost:4000)                │
│        └─ 微信公众号源                            │
│                                                  │
│  ☁️ 云服务器 (8.135.37.159)                      │
│     └─ SFTP上传 /var/www/html/reports/          │
└──────────────────────────────────────────────────┘

```

## 🔧 启动流程

### 首次启动
```
1. 配置 .env 文件
   ↓
2. 启动 Docker 服务
   docker compose up -d
   ↓
3. 验证配置
   python3 verify.py
   ↓
4. 测试运行
   python3 daily_report_PRO_cloud.py
   ↓
5. 安装定时任务
   ./manage_cron.sh install
```

### 日常自动运行
```
每天 9:00 AM
   ↓
launchd 唤醒
   ↓
执行 daily_report_PRO_cloud.py
   ↓
采集 → 排序 → 分析 → 生成 → 上传
   ↓
日志记录到 logs/stdout.log
```

## 📊 文件大小和复杂度

```
主程序文件:
├── daily_report_PRO_cloud.py   881 行 (最完整)
├── daily_report_PRO_wechat.py  615 行
├── daily_report_PRO_server.py  420 行
└── rss_collector.py            324 行

核心模块:
├── article_ranker.py           226 行
└── wechat_publisher.py          87 行

总代码量: ~2,553 行
```

## 🔐 安全相关文件

```
.gitignore           (防止 .env 和日志被提交)
.env.example         (配置模板)
.ssh/id_rsa          (SSH密钥 - 不在项目中)
```

## 📝 日志和输出

```
logs/
├── stdout.log       (标准输出日志)
└── stderr.log       (错误日志)

reports/
└── AI_Daily_YYYYMMDD_HHMMSS.html
``` 
