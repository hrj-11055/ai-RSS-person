# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI-powered RSS aggregation and daily report generation system that:
1. Collects AI news from 58+ RSS sources (Twitter, tech blogs, WeChat official accounts, academic journals)
2. Ranks articles using a dual scoring system (source authority 60% + content relevance 40%)
3. Generates intelligent analysis using DeepSeek AI
4. Automatically uploads reports to cloud server via SFTP/HTTP/FTP
5. Runs daily via macOS launchd (default: 9:00 AM)

**Key Design Philosophy**: Cost optimization - intelligent filtering saves ~87% API costs by selecting top articles for AI analysis.

## Repository Structure

```
.
├── Core Modules
│   ├── article_ranker.py        # ArticleRanker class - dual scoring system
│   ├── rss_collector.py         # 4-strategy RSS fetching (rsshub/cffi/direct/noproxy)
│   └── wechat_publisher.py      # WeChat Official Account integration
│
├── Main Scripts
│   ├── daily_report_PRO_cloud.py    # Primary: collect→rank→analyze→upload
│   ├── daily_report_PRO_server.py   # Server-local version (future migration)
│   ├── daily_report_PRO_wechat.py   # WeChat publishing version
│   └── integrate_to_website.py      # SQLite integration with external website
│
├── Infrastructure
│   ├── docker-compose.yml           # RSSHub, Redis, MySQL, wewe-rss
│   └── com.aireport.daily.plist     # macOS launchd configuration
│
├── Utilities
│   ├── manage_cron.sh               # Cron task management (install/uninstall/status)
│   ├── verify.py                    # Environment and dependency checker
│   └── test_upload.py               # Cloud upload testing
│
└── Output
    ├── reports/                     # Generated HTML reports (auto-created)
    └── logs/                        # Scheduled task logs (auto-created)
```

## Core Architecture

### Data Flow

```
RSS Sources (58 feeds) → RSS Collection → Article Ranking → AI Analysis (DeepSeek) → HTML Report → Cloud Upload
```

### RSS Source Strategies

The system uses 4 different fetch strategies in `rss_collector.py`:

- **rsshub**: For Twitter/X and Chinese RSS via local RSSHub (localhost:1200)
- **cffi**: Using curl_cffi to bypass 403 blocks (e.g., AI News)
- **direct**: Direct connection via proxy for well-behaved sites (Google, OpenAI blogs)
- **noproxy**: Direct connection without proxy for academic sites (arxiv.org)

### Article Ranking System (`article_ranker.py`)

Dual scoring system (0-100 points):
- **Source Authority (60%)**: Predefined weights for each source (e.g., OpenAI Blog: 100, generic media: 65)
- **Content Relevance (40%)**: Keyword matching for high-value terms (model launches, funding, breakthroughs, CEO changes)

Sources with highest authority: official AI company blogs (OpenAI, Anthropic, DeepMind), AI leaders' Twitter accounts (Sam Altman, Geoffrey Hinton), and top academic sources (Arxiv).

### Main Programs

- **`daily_report_PRO_cloud.py`**: Primary script - collects, ranks, analyzes, generates HTML, and uploads to cloud server via SFTP/HTTP/FTP. **Use this for daily automated runs.**

- **`daily_report_PRO_server.py`**: Server-local version designed for future migration to run directly on cloud server (localhost report generation). Not currently used in production.

- **`daily_report_PRO_wechat.py`**: WeChat version that publishes reports to WeChat Official Account drafts instead of cloud server. Requires WeChat API credentials.

- **`integrate_to_website.py`**: Post-processing script that integrates generated reports into external RSS-Spider website system with SQLite database. Use after report generation if website integration is needed.

### Cost Tracking (`CostTracker` class)

Tracks DeepSeek API usage:
- Input tokens: ¥2/million
- Output tokens: ¥3/million
- Typical run: 50,000-100,000 tokens (¥0.15-0.30)
- Monthly cost: ~¥5-10 for daily runs

### Environment Variable Handling

The codebase uses two helper functions for environment variables:
- `get_required_env(key)`: Raises `ValueError` with helpful message if missing
- `get_optional_env(key, default)`: Returns default value if not set

**Critical**: Always load env vars with `load_dotenv()` before using them. Main scripts follow this pattern:
```python
from dotenv import load_dotenv
load_dotenv()
DEEPSEEK_API_KEY = get_required_env("DEEPSEEK_API_KEY")
```

## Development Commands

### Initial Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Copy and configure environment variables
cp .env.example .env
vim .env

# Verify installation
python3 verify.py
```

### Required Environment Variables

```bash
# Required
DEEPSEEK_API_KEY=sk-xxxxx

# Optional but recommended
PROXY_URL=http://127.0.0.1:7897
RSSHUB_HOST=http://localhost:1200

# Cloud server upload (for daily_report_PRO_cloud.py)
CLOUD_SERVER_HOST=8.135.37.159
CLOUD_SERVER_PORT=22
CLOUD_SERVER_USER=root
CLOUD_SERVER_KEY_PATH=/path/to/ssh/key
CLOUD_SERVER_REMOTE_PATH=/var/www/html/reports
UPLOAD_METHOD=sftp
```

### Docker Services

```bash
# Start all services (RSSHub, Redis, MySQL, wewe-rss)
docker compose up -d

# Check service status
docker ps

# View logs
docker logs rss-person-rsshub --tail 50

# Restart services
docker compose restart

# Stop services
docker compose down
```

**Services:**
- `rss-person-rsshub` (port 1200): Twitter and Chinese RSS sources
- `rss-person-redis`: RSSHub cache
- `rss-person-mysql`: wewe-rss database (optional - for WeChat sources)
- `rss-person-wewe-rss` (port 4000): WeChat Official Account sources (optional)

### Running the Report Generator

```bash
# Run the main cloud version (recommended)
python3 daily_report_PRO_cloud.py

# Run WeChat version
python3 daily_report_PRO_wechat.py

# Verify project configuration
python3 verify.py

# Test RSS source availability
python3 rss_collector.py
```

Output: HTML reports saved to `reports/` directory with filename format `AI_Daily_Report_YYYYMMDD_HHMMSS.html`

### macOS Launchd Management

```bash
# Install daily scheduled task (9:00 AM)
./manage_cron.sh install

# Uninstall scheduled task
./manage_cron.sh uninstall

# Check task status
./manage_cron.sh status

# View logs
./manage_cron.sh logs

# Manual test run
./manage_cron.sh test

# Edit schedule time
./manage_cron.sh edit
```

**Important**: The plist file path references must be absolute. `manage_cron.sh` handles copying to `~/Library/LaunchAgents/`. To modify schedule time, edit the `Hour` and `Minute` integers in `com.aireport.daily.plist` and reinstall.

### Testing Cloud Upload

```bash
# Test SFTP/HTTP upload functionality
python3 test_upload.py

# Test report generation and upload together
python3 test_upload_report.py
```

## Configuration Files

- **`.env`**: Environment variables (API keys, proxy settings, cloud server credentials)
- **`docker-compose.yml`**: Infrastructure services (RSSHub, Redis, MySQL, wewe-rss)
- **`com.aireport.daily.plist`**: macOS launchd configuration for scheduled execution
- **`requirements.txt`**: Python dependencies

## Code Organization

### Core Modules

- **`article_ranker.py`**: `ArticleRanker` class - calculates article scores based on source authority and keywords
- **`rss_collector.py`**: 4-strategy RSS fetching with automatic fallback (rsshub/cffi/direct/noproxy)
- **`wechat_publisher.py`**: WeChat Official Account publishing integration

### Logging System

All main scripts use a consistent logging setup (`setup_logger()` function):
- Configurable log level via `LOG_LEVEL` environment variable (DEBUG/INFO/WARNING/ERROR)
- Console output with structured formatting: `%(asctime)s - %(name)s - %(levelname)s - %(message)s`
- Timestamps for each log entry
- **Important**: Call `setup_logger(level=LOG_LEVEL)` AFTER loading env vars to respect LOG_LEVEL setting

### Error Handling

- RSS fetch failures are logged but don't stop execution (fault-tolerant design)
- AI API errors are caught and reported with full context
- Cloud upload failures generate warnings but preserve local reports
- Source-specific proxy strategy failures trigger automatic fallback (direct → cffi)
- Exception messages truncated to 100 chars to prevent log spam

### Main Script Structure Pattern

All main scripts follow this pattern:
```python
# 1. Logging setup
logger = setup_logger()

# 2. Load environment variables
load_dotenv()
DEEPSEEK_API_KEY = get_required_env("DEEPSEEK_API_KEY")

# 3. Reconfigure logger with LOG_LEVEL from env
logger = setup_logger(level=get_optional_env("LOG_LEVEL", "INFO"))

# 4. Initialize components
ranker = ArticleRanker()
cost_tracker = CostTracker()

# 5. Execute workflow
try:
    # RSS collection
    # Ranking
    # AI analysis
    # Report generation
    # Upload (if applicable)
except Exception as e:
    logger.error(f"Script failed: {e}")
    raise
```

## Integration Points

### External Systems

1. **DeepSeek AI API**: Used for article analysis and report generation
2. **Cloud Server (8.135.37.159)**: SFTP upload for public report hosting
3. **RSS-Spider Website** (`integrate_to_website.py`): SQLite database integration for website display
4. **WeChat API** (optional): Publishing to WeChat Official Account drafts

### Report Formats

- **HTML**: Primary format with embedded CSS
- Includes: introduction, ranked articles with AI analysis, original links, conclusion
- Responsive design with dark mode support

## Troubleshooting

### RSS Collection Failures

1. Check Docker services: `docker ps | grep rsshub`
2. Test RSSHub endpoint: `curl http://localhost:1200/twitter/user/OpenAI`
3. Restart RSSHub: `docker compose restart rsshub`
4. RSSHub needs 5-10 minutes after startup to build cache

### AI Analysis Failures

1. Verify DeepSeek API key in `.env`
2. Check API balance at https://platform.deepseek.com/
3. Test network connectivity to API endpoint

### Cloud Upload Failures

1. Test SSH connection: `ssh root@8.135.37.159`
2. Verify SSH key path or password
3. Test with: `python3 test_upload.py`

### Scheduled Task Not Running

1. Check status: `./manage_cron.sh status`
2. View logs: `./manage_cron.sh logs`
3. Ensure Mac wasn't asleep at scheduled time
4. Verify Python path in plist file matches `which python3`

## File Structure Notes

- **`reports/`**: Generated HTML reports (auto-created)
- **`logs/`**: Scheduled task logs (auto-created by manage_cron.sh)
- **MAC_CRON_GUIDE.md**: Detailed launchd configuration guide
- **CLOUD_UPLOAD_GUIDE.md**: Cloud server setup documentation
- **WEBSITE_INTEGRATION_GUIDE.md**: Instructions for integrating with RSS-Spider website

## Important Implementation Details

### RSS Fetching Strategy
The system uses 4 different fetch strategies per source in `rss_collector.py`:
1. **rsshub**: Routes through local RSSHub for Twitter/X and Chinese sources
2. **cffi**: Uses curl_cffi with browser impersonation to bypass 403 blocks
3. **direct**: Standard requests with proxy for well-behaved sites
4. **noproxy**: Direct connection without proxy for academic sites (arxiv.org)

**Critical**: Some sources require proxy (PROXY_URL), others explicitly bypass it. Strategies are pre-assigned per source in the sources list.

### Article Filtering Pipeline
1. **Collection Phase**: Fetches 3-5 articles per source from all 58+ RSS feeds
2. **Ranking Phase**: Applies dual scoring (source authority 60% + content relevance 40%)
3. **Selection Phase**: Only top MAX_ARTICLES_IN_REPORT (default: 20) articles proceed to AI analysis
4. **Analysis Phase**: Selected articles sent to DeepSeek API for intelligent summaries

This 3-stage filtering achieves ~87% cost savings vs analyzing all articles.

### Time Window
- Collects articles from past 24 hours only
- Uses date filtering during RSS parsing
- Timezone: Uses system local time for comparisons

### Cloud Upload Priority
1. **SSH Key Authentication** (CLOUD_SERVER_KEY_PATH): Preferred method
2. **Password Authentication** (CLOUD_SERVER_PASSWORD): Fallback if no key provided
3. Upload methods: SFTP (default), HTTP, or FTP (via UPLOAD_METHOD env var)

### macOS Launchd Quirks
- launchd does NOT run tasks if Mac is asleep at scheduled time
- Tasks run ONCE after wakeup if missed (not retroactively)
- plist file requires absolute paths (no `~` expansion)
- `manage_cron.sh` handles path resolution and copying to `~/Library/LaunchAgents/`

### RSSHub Cache Behavior
- RSSHub requires 5-10 minutes after startup to build cache
- First fetch after restart may be slow/empty
- Redis backend persists cache across container restarts
- Check with: `curl http://localhost:1200/twitter/user/OpenAI`

## Development Patterns

### Adding New RSS Sources

To add a new RSS source, edit the sources list in `rss_collector.py`:

```python
{
    "name": "New AI Blog",
    "url": "https://example.com/rss",
    "strategy": "direct",  # or "rsshub", "cffi", "noproxy"
    "weight": 75,  # Source authority score (0-100)
    "category": "tech"
}
```

**Strategy selection guide**:
- **rsshub**: Twitter/X, Chinese sites, sites with anti-crawling
- **cffi**: Sites that return 403 errors
- **direct**: Well-behaved blogs (Google, OpenAI, etc.)
- **noproxy**: Academic sites that block proxies (arxiv.org)

### Modifying Article Ranking

Adjust scoring in `article_ranker.py`:
- **Source weights**: Edit `source_weights` dict (60% of total score)
- **Keywords**: Edit `high_weight_keywords` list (40% of total score)
- **Thresholds**: Modify `calculate_score()` logic if needed

### Testing Changes

```bash
# Test RSS collection only
python3 rss_collector.py

# Test full pipeline
python3 daily_report_PRO_cloud.py

# Test upload only
python3 test_upload.py

# Verify all dependencies
python3 verify.py
```

### Debugging

Set `LOG_LEVEL=DEBUG` in `.env` for verbose output:
```bash
# Edit .env
LOG_LEVEL=DEBUG

# Run with debug logging
python3 daily_report_PRO_cloud.py
```

View logs for scheduled tasks:
```bash
# Real-time logs
./manage_cron.sh logs

# Log file location
logs/stdout.log  # Standard output
logs/stderr.log  # Error output
```
