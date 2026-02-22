# Twitter RSS 源修复方案

## 问题描述

Twitter 源无法使用，日志显示：
```
❌ Twitter 源获取失败
```

## 原因

当前配置的 `TWITTER_AUTH_TOKEN` 值：
```yaml
TWITTER_AUTH_TOKEN=51e551ff8318dd33286897285d4bf514d8250bec
```

**这个 token 已经过期**，Twitter API token 通常只有 1-2 周的有效期。

## 解决方案

### 方案 1：更新 Twitter Cookie（推荐）

**步骤**：
1. 打开 https://twitter.com 并登录
2. 按 F12 打开开发者工具
3. 切换到 Network 标签
4. 找到任意请求，查看 Request Headers
5. 复制完整的 `cookie` 字符串值（包含 auth_token）
6. 更新 docker-compose.yml

**如何复制 cookie**：
```bash
# 在 Network 标签中找到类似这样的值：
cookie: "ct0=abcde; auth_token=51e551ff8318dd33286897285d4bf514d8250bec; guest_id=v1; ..."
```

### 方案 2：暂时移除 Twitter 源

**修改 [lib/rss_collector.py](lib/rss_collector.py)**，注释掉 Twitter 源：
```python
# 临时注释掉 Twitter 源
# {"name": "OpenAI Twitter", "url": "/twitter/user/OpenAI", "strategy": STRATEGY_RSSHUB},
...
```

### 方案 3：使用公开 RSS �替代

可以使用公开的 Twitter RSS 源：
- [Nitter](https://nitter.rs) - 第三方 Twitter RSS
- [RSS Bridge](https://rssbridge.app/) - RSS 聚合器

## 受影响的源

| 源 | 说明 |
|------|------|------|
| OpenAI Twitter | 官方机构账号 |
| Google DeepMind | 官方机构账号 |
| Anthropic AI | 官方机构账号 |
| DeepSeek AI | 官方机构账号 |
| Sam Altman | 官方机构账号 |
| Geoffrey Hinton | 官方专家账号 |
| Yann LeCun | 官方机构账号 |
| Andrew Ng | 官方专家账号 |

## 更新 token 获取方式

Twitter API v2 的 token 获取方式已改变：
1. 打开 Twitter 已登录状态
2. 使用浏览器开发者工具获取
3. 不再是简单的 `auth_token` 值

## Docker Compose 更新命令

```bash
# 停止容器
docker compose down

# 重新构建并启动（会获取新 token）
docker compose up -d --force-recreate

# 仅重启 RSSHub 服务
docker compose restart rsshub
```
