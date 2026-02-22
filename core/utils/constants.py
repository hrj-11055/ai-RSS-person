"""
Constants for AI-RSS-PERSON project.

Centralized location for all magic numbers and configuration values.
Extracted from various scripts to eliminate duplication.
"""

# ================= RSS Fetching =================
DEFAULT_MAX_ITEMS_PER_SOURCE = 5
DEFAULT_FETCH_TIMEOUT = 120  # 增加超时时间以适应公共 RSSHub 实例访问
DEFAULT_RETRY_DELAY = 1

# RSS Strategies
STRATEGY_RSSHUB = "rsshub"
STRATEGY_CFFI = "cffi"
STRATEGY_DIRECT = "direct"
STRATEGY_NOPROXY = "noproxy"

# ================= Article Ranking =================
DEFAULT_MAX_ARTICLES_IN_REPORT = 20
DEFAULT_SOURCE_WEIGHT_MIN = 50
DEFAULT_SOURCE_WEIGHT_MAX = 100

# Scoring weights (for dual scoring system)
SOURCE_AUTHORITY_WEIGHT = 0.60  # 60% from source authority
CONTENT_RELEVANCE_WEIGHT = 0.40  # 40% from content relevance

# ================= AI Analysis =================
DEFAULT_AI_MODEL = "deepseek-chat"
DEFAULT_AI_BASE_URL = "https://api.deepseek.com"
DEFAULT_MAX_TOKENS = 2000
DEFAULT_TEMPERATURE = 0.7

# Prompt types
PROMPT_TYPE_SUMMARY = "summary"
PROMPT_TYPE_DETAILED = "detailed"

# ================= Cost Tracking =================
INPUT_TOKEN_PRICE_PER_MILLION = 2.0  # CNY (DeepSeek)
OUTPUT_TOKEN_PRICE_PER_MILLION = 3.0  # CNY (DeepSeek)

# ================= Output =================
DEFAULT_OUTPUT_DIR = "reports"
DEFAULT_LOG_LEVEL = "INFO"

# Output formats
FORMAT_HTML = "html"
FORMAT_MARKDOWN = "markdown"
FORMAT_JSON = "json"

# ================= Cloud Upload =================
DEFAULT_CLOUD_SERVER_HOST = "8.135.37.159"
DEFAULT_CLOUD_SERVER_PORT = 22
DEFAULT_CLOUD_SERVER_USER = "root"
DEFAULT_CLOUD_SERVER_REMOTE_PATH = "/var/www/html/reports"
DEFAULT_CLOUD_SERVER_JSON_REMOTE_PATH = "/var/www/json/report"

# Upload methods
UPLOAD_METHOD_SFTP = "sftp"
UPLOAD_METHOD_HTTP = "http"
UPLOAD_METHOD_FTP = "ftp"
DEFAULT_UPLOAD_METHOD = "sftp"

# ================= RSSHub =================
# 默认使用本地部署的 RSSHub（需要先启动 docker-compose up rsshub）
# 本地部署更稳定，不受公共实例限流影响
DEFAULT_RSSHUB_HOST = "http://localhost:1200"
# 如需使用公共实例，可设置为: https://rsshub.pseudoyu.com

# ================= Time =================
# Time window for article collection (hours)
ARTICLE_TIME_WINDOW_HOURS = 24

# ================= Date Format =================
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"
FILENAME_DATETIME_FORMAT = "%Y%m%d_%H%M%S"

# ================= Error Messages =================
ERROR_MISSING_ENV_VAR = "❌ 缺少必需的环境变量: {key}\n请在 .env 文件中设置 {key}=your_value_here"
ERROR_FETCH_FAILED = "❌ 抓取失败: {source} - {error}"
ERROR_API_FAILED = "❌ AI分析失败: {error}"
ERROR_UPLOAD_FAILED = "❌ 上传失败: {error}"

# ================= Success Messages =================
SUCCESS_FETCH_COMPLETE = "✅ RSS收集完成: {total}篇文章"
SUCCESS_ANALYSIS_COMPLETE = "✅ AI分析完成"
SUCCESS_REPORT_GENERATED = "✅ 报告生成完成: {filename}"
SUCCESS_UPLOAD_COMPLETE = "✅ 文件上传成功"

# ================= Warning Messages =================
WARNING_SOURCE_FAILED = "⚠️ 源 {source} 抓取失败: {error}"
WARNING_NO_ARTICLES = "⚠️ 未找到符合条件的文章"
