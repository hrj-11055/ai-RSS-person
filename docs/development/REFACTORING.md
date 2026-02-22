# AI-RSS-PERSON 重构总结

本文档记录了从 v1.x 到 v2.0 的重构过程和成果。

---

## 重构目标

1. **消除重复代码** - 删除跨 4 个主脚本的 ~2000 行重复代码
2. **模块化架构** - 将业务逻辑抽离到独立的 lib/ 模块
3. **改进可维护性** - 清晰的目录结构和职责分离
4. **可持续迭代** - 为未来扩展打下基础

---

## 重构成果

### 代码消除统计

| 阶段 | 消除代码 | 说明 |
|------|----------|------|
| Phase 1: 共享工具 | ~276 行 | 提取 logger, env, cost_tracker, constants |
| Phase 2: 业务逻辑模块 | ~756 行 | 主脚本精简（cloud: -570行, wechat: -186行）|
| **总计** | **~1032 行** | **约 50% 的重复代码被消除** |

### 新增模块（lib/）

| 模块 | 代码行数 | 功能 |
|------|----------|------|
| [rss_collector.py](../lib/rss_collector.py) | 440 行 | RSS 采集，4 种抓取策略 |
| [ai_analyzer.py](../lib/ai_analyzer.py) | 434 行 | AI 分析（DeepSeek API） |
| [report_generator.py](../lib/report_generator.py) | 533 行 | 报告生成（MD/JSON/HTML） |
| [publishers/cloud_publisher.py](../lib/publishers/cloud_publisher.py) | 348 行 | 云发布器（SFTP/HTTP/FTP） |
| [publishers/local_publisher.py](../lib/publishers/local_publisher.py) | 215 行 | 本地发布器 |

### 主脚本精简

| 脚本 | 原行数 | 新行数 | 减少 | 减少比例 |
|------|--------|--------|------|----------|
| [daily_report_PRO_cloud.py](../daily_report_PRO_cloud.py) | 856 行 | 286 行 | -570 行 | **-67%** |
| [daily_report_PRO_wechat.py](../daily_report_PRO_wechat.py) | 562 行 | 376 行 | -186 行 | **-33%** |

---

## 目录结构变化

### 重构前
```
ai-RSS-person/
├── daily_report_PRO_cloud.py    # 856 行，包含所有逻辑
├── daily_report_PRO_wechat.py   # 562 行，大量重复
├── daily_report_PRO_server.py   # 已删除
├── rss_collector.py             # 独立模块，保留
├── article_ranker.py            # 独立模块，保留
└── wechat_publisher.py          # 独立模块，保留
```

### 重构后
```
ai-RSS-person/
├── core/                         # 新增：核心工具
│   └── utils/
│       ├── logger.py             # 日志设置
│       ├── env.py                # 环境变量工具
│       ├── cost_tracker.py       # 成本追踪
│       └── constants.py          # 常量定义
│
├── lib/                          # 新增：业务逻辑
│   ├── rss_collector.py          # 重构：4 种抓取策略
│   ├── ai_analyzer.py            # 新增：AI 分析
│   ├── report_generator.py       # 新增：报告生成
│   └── publishers/
│       ├── cloud_publisher.py    # 新增：云发布
│       └── local_publisher.py    # 新增：本地发布
│
├── daily_report_PRO_cloud.py     # 精简：286 行（-67%）
├── daily_report_PRO_wechat.py    # 精简：376 行（-33%）
├── rss_collector.py              # 保留
├── article_ranker.py             # 保留
└── wechat_publisher.py           # 保留
│
└── docs/                         # 新增：文档重组
    ├── user/                     # 用户文档
    ├── architecture/             # 技术文档（归档）
    └── development/              # 开发文档
```

---

## Phase 1: 共享工具提取

### 创建的文件

**core/utils/logger.py**
```python
def setup_logger(name: str = __name__, level: str = "INFO") -> logging.Logger:
    """配置并返回 logger 实例"""
```

**core/utils/env.py**
```python
def get_required_env(key: str) -> str:
    """获取必需的环境变量，否则抛出 ValueError"""

def get_optional_env(key: str, default: str = "") -> str:
    """获取可选的环境变量，返回默认值"""

def get_int_env(key: str, default: int) -> int:
    """获取整数类型的环境变量"""

def get_bool_env(key: str, default: bool = False) -> bool:
    """获取布尔类型的环境变量"""

def get_list_env(key: str, default: list = None) -> list:
    """获取列表类型的环境变量（逗号分隔）"""
```

**core/utils/cost_tracker.py**
```python
class CostTracker:
    """追踪 API 使用量和成本"""

    def add(self, usage) -> None:
        """添加 token 使用量"""

    def report(self) -> str:
        """生成成本报告"""

    def reset(self) -> None:
        """重置追踪器"""
```

**core/utils/constants.py**
```python
# RSS 采集
DEFAULT_MAX_ITEMS_PER_SOURCE = 5
DEFAULT_FETCH_TIMEOUT = 30
DEFAULT_RSSHUB_HOST = "http://localhost:1200"

# 抓取策略
STRATEGY_RSSHUB = "rsshub"
STRATEGY_CFFI = "cffi"
STRATEGY_DIRECT = "direct"
STRATEGY_NOPROXY = "noproxy"

# AI 分析
DEFAULT_AI_MODEL = "deepseek-chat"
DEFAULT_AI_BASE_URL = "https://api.deepseek.com"

# 输出
DEFAULT_OUTPUT_DIR = "reports"
DEFAULT_LOG_LEVEL = "INFO"

# 云服务器
DEFAULT_CLOUD_SERVER_HOST = ""
DEFAULT_CLOUD_SERVER_PORT = 22
# ... 更多常量
```

### 影响的文件
- [daily_report_PRO_cloud.py](../daily_report_PRO_cloud.py) - 移除 96 行重复代码
- [daily_report_PRO_wechat.py](../daily_report_PRO_wechat.py) - 移除 95 行重复代码
- [daily_report_PRO_server.py](../daily_report_PRO_server.py) - 已删除

---

## Phase 2: 业务逻辑提取

### lib/rss_collector.py

**重构内容**：
- 将 93 行的 `fetch_rss()` 函数拆分为多个方法
- 4 种抓取策略独立实现
- 时间窗口过滤逻辑独立

**关键方法**：
```python
class RSSCollector:
    def collect_all(self) -> List[Dict]:
        """从所有源采集文章"""

    def _fetch_with_strategy(self, url, strategy, source_name) -> Optional[bytes]:
        """使用指定策略抓取"""

    def _fetch_rsshub(self, route) -> Optional[bytes]:
        """策略：RSSHub"""

    def _fetch_cffi(self, url) -> Optional[bytes]:
        """策略：CFFI（绕过 403）"""

    def _fetch_direct(self, url) -> Optional[bytes]:
        """策略：直连（支持代理）"""

    def _fetch_noproxy(self, url) -> Optional[bytes]:
        """策略：直连（不走代理）"""

    def _parse_feed(self, content, source) -> List[Dict]:
        """解析和过滤文章"""

    def _is_within_time_window(self, entry) -> bool:
        """时间窗口过滤（24h）"""
```

### lib/ai_analyzer.py

**重构内容**：
- 将 173 行的 `analyze_with_ai()` 函数拆分为多个方法
- Prompt 模板作为类常量
- JSON 验证逻辑独立

**关键方法**：
```python
class AIAnalyzer:
    SUMMARY_PROMPT_TEMPLATE = "..."      # 类常量
    DETAILED_PROMPT_TEMPLATE = "..."      # 类常量
    REQUIRED_FIELDS = [...]               # 类常量

    def analyze_single(self, article, prompt_type="detailed") -> Optional[Dict]:
        """分析单篇文章"""

    def analyze_batch(self, articles, prompt_type="detailed") -> List[Dict]:
        """批量分析"""

    def _build_prompt(self, article, prompt_type) -> str:
        """构建 Prompt"""

    def _call_api(self, prompt):
        """调用 DeepSeek API"""

    def _parse_json_response(self, content, article) -> Optional[Dict]:
        """解析 JSON 响应"""

    def _validate_result(self, result, article) -> Dict:
        """验证必需字段"""

    def get_cost_report(self) -> str:
        """获取成本报告"""
```

### lib/report_generator.py

**重构内容**：
- 从主脚本提取 HTML 生成逻辑
- 支持 Markdown（默认）、JSON、HTML 格式
- YYYY-MM-DD.md 文件名格式

**关键方法**：
```python
class ReportGenerator:
    def generate_markdown(self, articles, title=None, date_str=None) -> str:
        """生成 Markdown 报告（默认格式）"""

    def generate_html(self, articles, title=None, date_str=None) -> str:
        """生成 HTML 报告"""

    def save_markdown(self, articles, filename=None) -> str:
        """保存 Markdown（YYYY-MM-DD.md 格式）"""

    def save_default(self, articles, markdown_filename=None, json_filename=None) -> Dict[str, str]:
        """保存默认格式（Markdown + JSON）"""
```

### lib/publishers/cloud_publisher.py

**重构内容**：
- 从 [daily_report_PRO_cloud.py](../daily_report_PRO_cloud.py) 提取 `CloudUploader` 类
- 支持 SFTP、HTTP、FTP 三种上传方式

**关键方法**：
```python
class CloudPublisher:
    def upload(self, local_file, remote_filename, remote_path=None) -> bool:
        """上传文件（根据配置选择方式）"""

    def upload_via_sftp(self, local_file, remote_filename, remote_path) -> bool:
        """SFTP 上传"""

    def upload_via_http(self, local_file, remote_filename) -> bool:
        """HTTP POST 上传"""

    def upload_via_ftp(self, local_file, remote_filename, remote_path) -> bool:
        """FTP 上传"""
```

### lib/publishers/local_publisher.py

**重构内容**：
- 提取本地文件保存逻辑
- 支持 HTML、Markdown、JSON、Text 格式

**关键方法**：
```python
class LocalPublisher:
    def save_html(self, content, filename=None) -> str:
        """保存 HTML"""

    def save_markdown(self, content, filename=None) -> str:
        """保存 Markdown"""

    def save_json(self, articles_data, date_str=None, filename=None) -> str:
        """保存 JSON"""

    def save_text(self, content, filename=None) -> str:
        """保存纯文本"""
```

---

## Phase 5: 文档重组

### 文档分类

**用户文档** (docs/user/)
- README.md - 完整使用指南
- CLOUD_UPLOAD_GUIDE.md - 云服务器配置
- MAC_CRON_GUIDE.md - macOS 定时任务
- WEBSITE_INTEGRATION_GUIDE.md - 网站集成
- TWITTER_COOKIE_GUIDE.md - Twitter Cookie

**技术文档** (docs/architecture/)
- PROJECT_FLOWCHART.md - 原始流程图
- PROJECT_FLOWCHART_VISUAL.md - 可视化流程图

**开发文档** (docs/development/)
- CLAUDE.md - Claude Code 使用指南
- REFACTORING.md - 本文档

---

## 设计原则

### 1. 单一职责原则
每个模块只负责一个功能：
- `rss_collector.py` - 只负责 RSS 采集
- `ai_analyzer.py` - 只负责 AI 分析
- `report_generator.py` - 只负责报告生成
- `publishers/` - 只负责发布

### 2. 开闭原则
- 通过继承和组合扩展功能
- 不修改原有代码即可添加新的发布方式

### 3. 依赖注入
- 所有模块通过构造函数接收配置
- 环境变量集中管理（core/utils/constants.py）

### 4. 错误处理
- 每个模块独立处理异常
- 日志记录详尽（使用 setup_logger）

---

## 使用示例

### 使用新的模块化架构

```python
from lib.rss_collector import RSSCollector
from lib.ai_analyzer import AIAnalyzer
from lib.report_generator import ReportGenerator
from lib.publishers.cloud_publisher import CloudPublisher

# 1. 采集
collector = RSSCollector()
articles = collector.collect_all()

# 2. 分析
analyzer = AIAnalyzer()
analyzed = analyzer.analyze_batch(articles[:20])

# 3. 生成报告
generator = ReportGenerator()
md_path = generator.save_markdown(analyzed)

# 4. 发布到云端
publisher = CloudPublisher()
publisher.upload(md_path, "2026-02-11.md")
```

---

## 未来改进方向

### 可选扩展
1. **配置外部化** - 将 RSS 源配置移到 YAML 文件
2. **更多发布方式** - 支持 GitHub Pages、Telegram 等
3. **AI 提供商切换** - 支持 OpenAI、Claude 等其他 API
4. **国际化** - 支持多语言报告

### 已废弃的计划
- ~~Phase 3: 工作流系统~~ - 对于相对简单的日报生成流程属于过度设计
- ~~Phase 4: 统一入口点~~ - 当前两个脚本（cloud/wechat）功能不同，分开更清晰

---

## Phase 6: 统一工作流简化 (2026-02-11)

### 背景

原有的多任务定时系统过于复杂：
- 3 个独立的定时任务（9:00, 8:30, 9:10）
- 用户需要配置多个任务
- 任务间协调困难

### 改进内容

#### 1. 统一 9:00 AM 任务

**修改文件**: [daily_report_PRO_cloud.py](../daily_report_PRO_cloud.py)

集成邮件发送到主流程：
```python
# JSON 上传成功后，自动发送邮件
if self.cloud_publisher.upload(local_file, remote_filename, CLOUD_SERVER_JSON_REMOTE_PATH):
    logger.info("✅ JSON 报告已成功上传到云服务器")

    # 触发邮件发送（JSON→MD→邮件）
    subprocess.run(['python3', 'daily_email_sender.sh'], ...)
```

#### 2. 简化管理脚本

**修改文件**: [manage_cron.sh](../manage_cron.sh)

移除多任务选项，简化为：
```bash
./manage_cron.sh install   # 安装唯一任务
./manage_cron.sh uninstall # 卸载任务
./manage_cron.sh test       # 测试完整流程
./manage_cron.sh test-email # 测试邮件发送
```

#### 3. 归档废弃配置文件

移至 `archive/`：
- `com.aireport.email.plist` (旧的 8:30 邮件任务)
- `com.aireport.daily.email.plist` (旧的 9:10 组合任务)

#### 4. 更新文档

**修改文件**: [docs/user/MAC_CRON_GUIDE.md](docs/user/MAC_CRON_GUIDE.md)

- 移除多任务说明
- 添加完整工作流程图
- 新增邮件发送故障排查
- 更新环境配置要求

### 新的工作流程

```
每天 9:00 AM 自动执行：
① 收集 RSS 文章（58+ 源）
② 双重评分排序（源权威性 60% + 内容相关性 40%）
③ AI 分析（DeepSeek API）
④ 生成 Markdown 报告 → 保存本地 (reports/YYYY-MM-DD.md)
⑤ 生成 JSON 数据 → 上传云服务器
⑥ 转换 JSON 为 Markdown → 发送邮件
```

### 优势

1. **简化配置** - 只需安装一个任务
2. **原子性** - 所有步骤在一个流程中完成
3. **易于调试** - 单一日志文件记录完整流程
4. **用户友好** - 清晰的命令和状态反馈

---

---

## Phase 7: 清理旧文件 (2026-02-11)

### 归档的文件

为了保持项目整洁，归档了以下旧文件到 `archive/` 目录：

#### 废弃的脚本
- `daily_report_PRO.py` - 旧的单文件版本（包含硬编码 API key，存在安全隐患）
- `rss_collector.py` (根目录) - 旧版本，已被 `lib/rss_collector.py` 替代

#### 废弃的测试文件
- `test_upload.py` - 旧的 SFTP 上传测试
- `test_upload_report.py` - 旧的报告上传测试

#### 废弃的配置文件
- `com.aireport.email.plist` - 旧的 8:30 邮件任务配置
- `com.aireport.daily.email.plist` - 旧的 9:10 组合任务配置

### 保留的文件

以下文件仍在使用，保留在根目录：
- `daily_report_PRO_cloud.py` - 主脚本（云服务器上传）
- `daily_report_PRO_wechat.py` - 微信发布版本
- `article_ranker.py` - 文章排序模块
- `email_sender.py` - 邮件发送模块
- `wechat_publisher.py` - 微信公众号发布（被 wechat 版本使用）

### 新的测试文件

`tests/` 目录包含完整的测试套件：
- `test_rss_collector.py` - RSS 采集测试
- `test_article_ranker.py` - 文章排序测试
- `test_ai_analyzer.py` - AI 分析测试
- `test_report_generator.py` - 报告生成测试
- `run_tests.py` - 测试运行脚本
- `README.md` - 测试文档

---

## 总结

本次重构成功：
- ✅ 消除了 ~1000 行重复代码
- ✅ 建立了清晰的模块化架构
- ✅ 提升了代码可维护性和可扩展性
- ✅ 重组了文档结构
- ✅ 简化了定时任务配置（3个任务 → 1个任务）
- ✅ 创建了完整的测试套件（50 个测试，全部通过）
- ✅ 归档了旧文件，保持项目整洁
- ✅ 为可持续迭代打下基础

---

**重构完成日期**: 2026-02-11
**版本**: v2.1.0
**最后更新**: 清理旧文件 + 测试套件

---

## 📚 相关文档

- **[REFACTORING_EXPERIENCE.md](REFACTORING_EXPERIENCE.md)** - 重构经验总结（遇到的问题、解决方案、最佳实践）
- **[CLAUDE.md](CLAUDE.md)** - Claude Code 使用指南
- **[../user/README.md](../user/README.md)** - 用户文档入口
