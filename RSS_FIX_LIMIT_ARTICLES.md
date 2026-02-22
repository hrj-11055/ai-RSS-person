# 每 RSS 源限制最新 3 篇文章修复

## 修改说明

修改了 [lib/rss_collector.py](lib/rss_collector.py) 中的 `_parse_feed` 方法（第 315-327 行）：

**修改前**：
```python
for entry in candidates:
    # 时间过滤
    if not self._is_within_time_window(entry):
        continue
```

**修改后**：
```python
for entry in candidates:
    # 时间过滤（仅在有明确时间戳时进行）
    if entry.get('published_parsed') or entry.get('updated_parsed'):
        if not self._is_within_time_window(entry):
            continue
```

## 原理

- **没有时间戳的文章**：直接通过（假设是最近的）
- **有时间戳的文章**：只有在明确时间戳时才进行时间窗口过滤

## 效果

| RSS 源类型 | 采集策略 |
|-----------|----------|
| 每个源 | 获取前 3 篇 |
| 时间过滤 | 仅对有时间戳的文章生效 |

## 受益

1. **确保获取最新内容**：每个源只获取最新的几篇文章
2. **减少无效文章**：没有时间戳的旧文章不会被错误过滤
3. **提高效率**：减少处理的文章总数

## 需要注意

如果某个 RSS 源长时间不更新，可能会一直获取到同样的旧文章。对于这种情况，可以考虑：
1. 调整 `max_items_per_source` 参数
2. 或者使用更细粒度的时间窗口（如 12 小时）

## 测试

```bash
# 重新生成 2-15 报告
python3 daily_report_PRO_cloud.py
```
