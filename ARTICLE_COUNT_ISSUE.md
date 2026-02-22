# 2-15 报告文章数异常分析

## 问题描述

2-15 的报告只包含 **13 篇文章**，但实际采集了 20 篇文章。

## 原因分析

### 1. 时间窗口过滤

时间窗口设置：24 小时
- 报告生成时间：2026-02-15 10:19
- 截止时间：2026-02-14 07:00
- 采集时间：2026-02-14 08:47

### 2. 时间戳格式问题

测试发现报告中文章缺少 `published_parsed` 时间戳：
```python
# 所有文章都没有时间戳，被过滤掉了
in_window = 0/20  # 时间窗口内为 0
```

**原因**：新增加的 27 个 AI RSS feeds 可能没有标准的时间戳格式，导致文章被时间窗口过滤掉。

## 解决方案

### 方案 A：禁用时间窗口过滤（临时）

修改 `daily_report_PRO_cloud.py`：
```python
# 添加时间窗口参数
collector = RSSCollector(time_window_hours=0)  # 不过滤
```

### 方案 B：检查并修复 RSS feeds 的时间戳

对于没有时间戳的源，需要在 `rss_collector.py` 中：
1. 检查文章是否有时间戳
2. 如果没有，假设为当前时间
3. 或者使用 `updated_parsed` 作为备选

## 受影响的 RSS 源

新增加的 27 个 AI feeds 中，部分源可能没有正确的时间戳：
- AI Roadmap (Medium)
- Machine Learning Mastery
- Microsoft ML
- AWS ML
- DataRobot
- DeepMind
- Sentient
- ArchieAI (Medium)
- 等等...

## 建议

1. **测试单个源**：
```bash
# 测试特定源是否有时间戳
python3 -c "
import feedparser
from lib.rss_collector import DEFAULT_SOURCES

for source in DEFAULT_SOURCES[:3]:
    feed = feedparser.parse(f'{source['url']}')
    print(f'{source['name']}: {len(feed.entries)} 篇')
    for entry in feed.entries[:3]:
        has_time = 'published_parsed' in entry or 'updated_parsed' in entry
        print(f'  - 有时间戳: {has_time}')
"
```

2. **临时方案**：使用 0 小时时间窗口重新生成报告

3. **长期方案**：优化 `rss_collector.py` 的时间戳处理逻辑

## 相关文件

- [lib/rss_collector.py](lib/rss_collector.py) - DEFAULT_SOURCES
- [daily_report_PRO_cloud.py](daily_report_PRO_cloud.py) - 主脚本
- [core/utils/constants.py](core/utils/constants.py) - 时间窗口配置
