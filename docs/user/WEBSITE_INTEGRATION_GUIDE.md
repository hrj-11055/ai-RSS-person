# RSS-Person报告网站集成指南

## 📋 功能说明

`integrate_to_website.py` 脚本用于将RSS-Person生成的报告自动集成到RSS-Spider网站系统中，实现：

1. ✅ **自动数据库插入**：将报告记录插入到RSS-Spider的SQLite数据库
2. ✅ **文件自动复制**：将HTML报告复制到网站可访问的`output/`目录
3. ✅ **网站自动展示**：报告会自动出现在http://localhost:8001的报告页面
4. ✅ **支持批量处理**：可以一次性集成所有历史报告

---

## 🚀 快速开始

### 方法1：自动集成（推荐）

`daily_report_PRO_cloud.py` 已配置为在每次生成报告后自动调用集成脚本。

```bash
# 运行报告生成（会自动集成）
python3 daily_report_PRO_cloud.py
```

### 方法2：手动集成最新报告

```bash
# 集成最新的一个报告
python3 integrate_to_website.py
```

### 方法3：批量集成所有报告

```bash
# 集成所有未集成的历史报告
python3 integrate_to_website.py --all
```

---

## ⚙️ 配置说明

在 `integrate_to_website.py` 中的配置项：

```python
# RSS-spider项目路径（自动检测）
RSS_SPIDER_PATH = Path(__file__).parent.parent

# 数据库路径
DB_PATH = RSS_SPIDER_PATH / "data" / "rss_saas.db"

# 报告源目录（RSS-person生成的报告）
REPORTS_SOURCE_DIR = RSS_PERSON_PATH / "reports"

# 目标目录（网站访问目录）
OUTPUT_TARGET_DIR = RSS_SPIDER_PATH / "output"

# 分配给RSS-person报告的用户名
USERNAME = "admin"  # 可以改为任何用户名
```

### 用户说明

- 默认使用 `admin` 用户
- 如果用户不存在，脚本会自动创建
- 可以修改为任何现有用户名（如 `test`, `alice` 等）

---

## 📊 工作流程

```
RSS-Person生成报告
        ↓
┌───────────────────────────────┐
│  daily_report_PRO_cloud.py    │
│  1. 采集RSS资讯               │
│  2. AI分析排序                │
│  3. 生成HTML报告              │
│  4. 上传云服务器  ←─────┐     │
│  5. 调用集成脚本 ────────┼────┤
└───────────────────────────────┘ │
                                  │
                    ┌─────────────┘
                    ↓
┌───────────────────────────────────┐
│   integrate_to_website.py        │
│   1. 提取报告元数据               │
│   2. 检查是否已存在               │
│   3. 复制HTML到output/{username}/ │
│   4. 插入数据库记录               │
└───────────────────────────────────┘
                    ↓
        ┌───────────────┴───────────────┐
        ↓                               ↓
   网站可访问                      数据库记录
   /static/{user}/文件名.html       reports表
        ↓                               ↓
        └───────────┬───────────────────┘
                    ↓
            网站前端显示
    http://localhost:8001 的报告页面
```

---

## 📝 集成后效果

### 1. 数据库记录

报告会被插入到 `reports` 表：

```sql
SELECT * FROM reports WHERE user_id = (SELECT id FROM users WHERE username='admin') ORDER BY generated_at DESC LIMIT 5;
```

### 2. 文件系统

HTML文件被复制到：

```
RSS-spider/output/admin/2026-02-05_AI.html
```

### 3. 网站访问

- **前端页面**: http://localhost:8001 (登录后查看报告)
- **直接访问**: http://localhost:8001/static/admin/2026-02-05_AI.html
- **API查询**: `GET /api/v1/reports/{username}`

---

## 🧪 测试验证

### 验证1：检查数据库

```bash
sqlite3 ../RSS-spider/data/rss_saas.db "SELECT id, title, items_count, generated_at FROM reports ORDER BY generated_at DESC LIMIT 3;"
```

预期输出：
```
17|全球AI日报 | 2026-02-05|15|2026-02-05 09:00:00
```

### 验证2：检查文件

```bash
ls -lh ../RSS-spider/output/admin/
```

预期输出：
```
-rw-r--r--  1 user  staff   50K Feb  5 09:00 2026-02-05_AI.html
```

### 验证3：访问网站

```bash
# 1. 启动API服务器
cd ../RSS-spider
python run_api.py

# 2. 打开浏览器访问
open http://localhost:8001

# 3. 登录后访问报告页面
# 用户名: admin
# 密码: (任意，因为创建时没有密码)
```

---

## 🔧 故障排查

### 问题1：数据库连接失败

**错误信息**: `sqlite3.OperationalError: unable to open database file`

**解决方法**:
```bash
# 检查数据库文件是否存在
ls -la ../RSS-spider/data/rss_saas.db

# 如果不存在，初始化数据库
cd ../RSS-spider
./rss-saas init
```

### 问题2：用户不存在且无法创建

**错误信息**: 创建用户失败

**解决方法**:
```bash
# 手动创建用户
cd ../RSS-spider
./rss-saas user create admin admin@example.com
```

### 问题3：HTML解析失败

**错误信息**: `⚠️ 解析HTML失败`

**解决方法**: 检查HTML文件格式是否正确，或手动提供元数据

```python
# 修改integrate_to_website.py中的extract_metadata_from_html函数
# 使用BeautifulSoup进行更可靠的解析
```

### 问题4：文件复制失败

**错误信息**: `[Errno 2] No such file`

**解决方法**:
```bash
# 确保output目录存在
mkdir -p ../RSS-spider/output/admin
```

---

## 📈 使用场景

### 场景1：日常自动运行

```bash
# 1. 安装Mac定时任务（每天9:00运行）
./manage_cron.sh install

# 2. 每天自动执行：
#    - 生成报告
#    - 上传云服务器
#    - 集成到网站 ← 新增功能
```

### 场景2：批量处理历史报告

```bash
# 集成所有历史报告（一次性）
python3 integrate_to_website.py --all
```

### 场景3：手动触发集成

```bash
# 生成报告后立即集成
python3 daily_report_PRO_cloud.py  # 自动集成

# 或单独运行集成
python3 integrate_to_website.py
```

---

## 🔄 更新现有报告

如果报告已存在，默认会跳过。强制更新：

```python
# 在integrate_to_website.py中修改check_report_exists函数
# 将"return result is not None"改为"return False"以强制更新
```

---

## 🎉 完成！

现在您的RSS-Person报告会自动：

1. ✅ 生成到 `reports/` 目录
2. ✅ 上传到云服务器 `8.135.37.159`
3. ✅ 集成到网站系统（数据库 + 文件）
4. ✅ 在前端页面显示

**享受自动化带来的便利！** 🚀
