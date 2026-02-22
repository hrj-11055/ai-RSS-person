# RSSHub 公开实例优化总结

## 完成的修改

### 1. 配置文件更新

**[.env](.env)**:
```bash
# 使用公开实例节省本地内存 (~379 MB)
RSSHUB_HOST=https://rsshub.pseudoyu.com
```

**[.env.example](.env.example)**:
```bash
# 更新推荐配置为公开实例
RSSHUB_HOST=https://rsshub.pseudoyu.com
```

**[docker-compose.yml](docker-compose.yml)**:
- 注释掉 RSSHub 和 Redis 服务
- 仅保留 MySQL + wewe-rss（微信公众号源）

**[lib/rss_collector.py](lib/rss_collector.py)**:
- 修复 `_fetch_rsshub` 方法，添加代理支持

**[core/utils/constants.py](core/utils/constants.py)**:
- 增加超时时间：30s → 60s

### 2. 测试结果

**公开实例测试**:
| 实例 | 状态 | 说明 |
|-------|------|------|
| rsshub.app | ❌ | Twitter 路由重定向到 404 |
| hub.slarker.me | ❌ | 返回 503 |
| **rsshub.pseudoyu.com** | ⚠️ | 可用但不稳定 |

**问题**:
- 第一个请求成功获取 OpenAI Twitter（3 篇文章）
- 后续请求出现连接超时
- 这是公开实例的常见问题（流量限制/带宽限制）

### 3. 当前状态

**✅ 工作正常**:
- 直接 RSS 源（100+ 个）正常采集
- AI 分析正常
- 报告生成成功
- JSON 上传成功
- 邮件发送成功

**⚠️ Twitter 源状态**:
- 公开实例不稳定，无法可靠采集
- 建议回退到本地部署或寻找其他解决方案

## 解决方案选项

### 方案 A：回退到本地部署（推荐）

```bash
# 1. 恢复 .env 配置
RSSHUB_HOST=http://localhost:1200

# 2. 更新 docker-compose.yml（取消注释 RSSHub 和 Redis）

# 3. 更新 Twitter Cookie（关键！）
# 打开 https://twitter.com，F12 开发者工具 → Network → Request Headers → cookie
# 复制 auth_token 值，更新到 docker-compose.yml 的 TWITTER_AUTH_TOKEN

# 4. 重启服务
docker compose up -d
```

### 方案 B：多实例轮换（高级）

修改 `rss_collector.py` 实现多实例轮换：
```python
RSSHUB_INSTANCES = [
    "https://rsshub.pseudoyu.com",
    "https://hub.slarker.me",
    # 添加更多实例...
]
```

### 方案 C：暂时移除 Twitter 源

注释掉 `DEFAULT_SOURCES` 中的 Twitter 源：
```python
# {"name": "OpenAI Twitter", "url": "/twitter/user/OpenAI", "strategy": STRATEGY_RSSHUB},
```

## 备份文件

- `.env.backup` - 原始环境变量配置
- `docker-compose.yml.backup` - 原始 Docker 配置

## 内存优化效果

如果采用公开实例方案：
- **本地 RSSHub + Redis**: ~379 MB
- **公开实例**: 0 MB
- **节省内存**: ~379 MB

但如果需要 Twitter 源，建议使用本地部署。
