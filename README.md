# AI-RSS-PERSON

> AI 驱动的 RSS 智能聚合与日报生成系统

从 150+ 权威信源中智能筛选 AI 行业资讯，通过 DeepSeek AI 分析生成结构化日报。

---

## 快速开始

### 方式 A：一键启动（推荐）

```bash
# 克隆项目
git clone https://github.com/yourusername/ai-RSS-person.git
cd ai-RSS-person

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
vim .env  # 设置 DEEPSEEK_API_KEY

# 一键启动
python daily_report.py
```

### 方式 B：Docker 启动

```bash
# 启动 Docker 服务（RSSHub）
docker compose up -d

# 运行日报生成
python daily_report.py
```

---

## 项目结构（v2.1）

```
ai-RSS-person/
├── config/                    # 配置文件（新增）
│   ├── sources.yaml          # RSS 源配置
│   └── weights.yaml          # 权重配置
│
├── core/                      # 核心工具模块
│   ├── config_manager.py     # 配置管理器（新增）
│   └── utils/                # 共享工具
│       ├── logger.py         # 日志
│       ├── env.py            # 环境变量
│       ├── cost_tracker.py   # 成本追踪
│       └── constants.py      # 常量
│
├── lib/                       # 业务逻辑模块
│   ├── rss_collector.py      # RSS 采集
│   ├── ai_analyzer.py        # AI 分析
│   ├── report_generator.py   # 报告生成
│   └── publishers/           # 发布策略
│       ├── cloud_publisher.py
│       └── local_publisher.py
│
├── scripts/                   # 辅助脚本
│   └── dev/                  # 开发调试工具
│       ├── test_twitter_source.py
│       └── manage_cron.sh
│
├── archive/                   # 归档代码
│   ├── daily_report_PRO.py   # 旧版本
│   └── ...
│
├── daily_report.py            # 统一入口（新增）
├── daily_report_PRO_cloud.py # 云服务器版本
├── daily_report_PRO_wechat.py # 微信版本
├── article_ranker.py          # 文章排序（已重构）
├── email_sender.py            # 邮件发送
└── docker-compose.yml         # Docker 服务
```

---

## 新功能 (v2.1)

### 配置外部化
- **RSS 源配置**：`config/sources.yaml` - 管理所有 RSS 源
- **权重配置**：`config/weights.yaml` - 管理源权重和关键词
- 支持启用/禁用源，无需修改代码

### 统一入口脚本
```bash
# 查看配置信息
python daily_report.py --config

# 测试模式（不发送邮件）
python daily_report.py --test

# 详细输出
python daily_report.py --verbose
```

---

## 使用方法

### 基本使用

```bash
# 运行完整流程（采集 → 分析 → 上传 → 邮件）
python daily_report.py

# 查看当前配置
python daily_report.py --config

# 测试模式（仅采集和分析）
python daily_report.py --test
```

### 配置管理

编辑 `config/sources.yaml` 添加或禁用 RSS 源：

```yaml
sources:
  - name: 新的 AI 博客
    url: https://example.com/feed
    strategy: direct
    enabled: true
    category: 研究博客
```

编辑 `config/weights.yaml` 调整权重：

```yaml
source_weights:
  OpenAI Blog: 100
  新的 AI 博客: 85

keywords:
  - 新术语
  - new-term
```

---

## 环境变量

### 必需配置

```bash
DEEPSEEK_API_KEY=sk-xxxxx          # DeepSeek API 密钥
```

### 可选配置

```bash
# 网络配置
PROXY_URL=http://127.0.0.1:7897    # 代理 URL（留空则不使用）
RSSHUB_HOST=http://localhost:1200  # RSSHub 地址

# 抓取设置
MAX_ITEMS_PER_SOURCE=5            # 每个源最多抓取文章数
MAX_ARTICLES_IN_REPORT=30         # 报告最多包含文章数

# 云服务器配置
CLOUD_SERVER_HOST=8.135.37.159    # 服务器地址
CLOUD_SERVER_PORT=22              # SSH 端口
CLOUD_SERVER_USER=root            # SSH 用户名
CLOUD_SERVER_KEY_PATH=/path/to/key # SSH 私钥路径
UPLOAD_METHOD=sftp                # 上传方式

# 输出配置
OUTPUT_DIR=reports                # 本地输出目录
LOG_LEVEL=INFO                    # 日志级别

# 邮件配置
SMTP_SERVER=smtp.qq.com
SMTP_PORT=465
SENDER_EMAIL=your@qq.com
SENDER_PASSWORD=your_auth_code
RECEIVER_EMAIL=recipient@example.com
```

---

## Docker 服务

```bash
# 启动所有服务
docker compose up -d

# 查看服务状态
docker ps

# 重启服务
docker compose restart rsshub

# 停止服务
docker compose down
```

**服务说明**：
- `rss-person-rsshub` (port 1200) - Twitter 和中文 RSS 源
- `rss-person-redis` - RSSHub 缓存

---

## 故障排查

### RSS 采集失败

```bash
# 检查源配置
python daily_report.py --config

# 测试 RSSHub 端点
curl http://localhost:1200/twitter/user/OpenAI

# 重启 RSSHub
docker compose restart rsshub
```

### 配置文件问题

```bash
# 验证 YAML 语法
python -c "import yaml; print(yaml.safe_load(open('config/sources.yaml')))"

# 查看启用的源
python daily_report.py --config
```

---

## 版本历史

### v2.1.0 (当前)
- ✅ 配置外部化（YAML）
- ✅ 统一入口脚本
- ✅ 重构权重系统
- ✅ 清理冗余脚本

### v2.0.0
- ✅ 模块化重构
- ✅ 消除重复代码
- ✅ 文档重组

---

## 许可证

MIT License
