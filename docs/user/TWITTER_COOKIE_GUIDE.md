# Twitter Cookie 配置指南

## 为什么需要配置 Twitter Cookie？

RSSHub 需要 Twitter Cookie 才能访问 Twitter/X 的内容。配置后可以订阅 13 个高价值 AI 相关 Twitter 账号：
- OpenAI, Google DeepMind, Anthropic AI, DeepSeek AI, Alibaba Qwen
- Sam Altman, Geoffrey Hinton, Yann LeCun, Yoshua Bengio
- Demis Hassabis, Andrew Ng, Jim Fan, Lex Fridman

**费用**: 完全免费（相比 Twitter API 的 $100/月）

---

## 📋 配置步骤

### 第一步：获取 Twitter Cookie

1. **打开 Twitter 并登录**
   ```
   访问 https://twitter.com 或 https://x.com
   确保已登录你的 Twitter 账号
   ```

2. **打开浏览器开发者工具**
   - **Chrome/Edge**: 按 `F12` 或 `Cmd+Option+I` (Mac)
   - **Firefox**: 按 `F12`
   - **Safari**: `Cmd+Option+I`（需先在偏好设置中启用开发菜单）

3. **切换到 Network（网络）标签**
   - 在开发者工具顶部找到 "Network" 标签并点击
   - 刷新页面 (F5 或 Cmd+R)

4. **找到 Cookie 值**
   - 在请求列表中找到任意请求（推荐找第一个请求，通常是首页）
   - 点击该请求
   - 在右侧面板找到 "Headers" (标头) 标签
   - 向下滚动找到 "Request Headers" 部分
   - 找到 `cookie:` 或 `Cookie:` 字段
   - 复制整个 cookie 值（很长的字符串）

5. **Cookie 格式示例**
   ```
   auth_token=xxxxx; ct0=xxxxx; twid=xxxxx; kdt=xxxxx; tweetdraftcreation=xxxxx; ...
   ```

**重要提示**:
- Cookie 中**必须**包含 `auth_token` 字段
- 通常还包含 `ct0` (csrf token) 和 `twid` (user ID)
- 不要包含引号或空格
- 复制完整的 cookie 字符串（以 `auth_token=` 开头到最后一个字段）

---

### 第二步：配置到 docker-compose.yml

我已经在 `docker-compose.yml` 中添加了 Twitter Cookie 配置项，现在需要填入你的 Cookie 值。

**编辑 docker-compose.yml**:

```yaml
  rsshub:
    image: diygod/rsshub:latest
    container_name: rss-person-rsshub
    ports:
      - "1200:1200"
    environment:
      - NODE_ENV=production
      - CACHE_TYPE=redis
      - REDIS_URL=redis://redis:6379
      # 👇 将下面的 xxxxx 替换为你从浏览器复制的完整 Cookie 值
      - TWITTER_COOKIE=auth_token=xxxxx; ct0=xxxxx; twid=xxxxx; ...
```

**替换步骤**:
1. 用文本编辑器打开 `docker-compose.yml`
2. 找到 `TWITTER_COOKIE=` 这一行
3. 将 `auth_token=xxxxx; ct0=xxxxx; twid=xxxxx; ...` 替换为你复制的完整 Cookie 值
4. 保存文件

**示例**:
```yaml
- TWITTER_COOKIE=auth_token=abc123def456...; ct0=789xyz012...; twid=u_12345...; kdt=ABCD...
```

---

### 第三步：重启 RSSHub 容器

配置完成后，需要重启 RSSHub 容器使配置生效：

```bash
# 进入项目目录
cd /Users/MarkHuang/ai-RSS-person

# 重启 RSSHub 容器
docker compose restart rsshub

# 等待 10 秒让容器完全启动
sleep 10

# 查看容器日志确认无错误
docker logs rss-person-rsshub --tail 20
```

**预期输出**:
```
✅ RSSHub 启动成功，无 Twitter 配置错误
```

---

### 第四步：验证配置是否成功

运行 RSS 源测试脚本：

```bash
python3 rss_collector.py
```

**预期结果**:
```
[1/55] OpenAI Twitter            | 策略: rsshub   ... ✅ 20条
[2/55] Google DeepMind           | 策略: rsshub   ... ✅ 15条
[3/55] Anthropic AI              | 策略: rsshub   ... ✅ 10条
...
```

如果看到 Twitter 源显示 `✅ XX条`，说明配置成功！

---

## 🔧 故障排除

### 问题 1: 仍然显示 "ConfigNotFoundError: Twitter API is not configured"

**原因**: Cookie 格式不正确或缺少必需字段

**解决方法**:
1. 确认 Cookie 包含 `auth_token` 字段
2. 确认整个 Cookie 在一行内（没有换行）
3. 确认没有多余的引号或空格
4. 尝试重新从浏览器复制 Cookie（Cookie 可能已过期）

### 问题 2: Twitter 源返回 503 错误

**原因**: Cookie 已过期或被 Twitter 撤销

**解决方法**:
1. 重新登录 Twitter
2. 按照第一步重新获取 Cookie
3. 更新 docker-compose.yml
4. 重启容器

### 问题 3: 某些 Twitter 账号能抓取，某些不能

**原因**: 部分账号可能设置了隐私保护或已被封禁

**解决方法**:
- 这是正常现象，RSSHub 只能访问公开的推文
- 私密账号或已封禁账号无法订阅

---

## 📝 Cookie 有效期说明

- **一般情况**: Cookie 有效期约 **1-2 周**
- **过期后**: 需要重新获取并更新配置
- **自动更新**: 暂不支持（建议每隔 1-2 周检查一次）

**提示**: 如果 Twitter 源突然全部失效，很可能是 Cookie 过期了。

---

## 🎯 配置完成后的收益

配置成功后，你的 AI 每日报告将包含以下额外内容：

### 高价值 Twitter 源 (13个)
- **官方账号**: OpenAI, Google DeepMind, Anthropic AI, DeepSeek AI, Alibaba Qwen
- **AI 大佬**: Sam Altman, Geoffrey Hinton, Yann LeCun, Yoshua Bengio, Demis Hassabis, Andrew Ng, Jim Fan, Lex Fridman

### 采集频率
- 每个账号采集最新 **3-5 条推文**
- 按时间排序，优先展示最新内容

### 权重提升
在文章排名系统中，Twitter 源的权重为 **70-100 分**（仅次于官方博客）

---

## 🔐 安全提示

1. **Cookie 是敏感信息**，包含你的登录凭证
2. **不要分享** Cookie 给他人
3. **不要提交** Cookie 到 Git 仓库
4. **定期更换**: Cookie 会过期，这是正常现象

**注意**: `docker-compose.yml` 包含敏感信息，建议添加到 `.gitignore`（如果尚未添加）。

---

## 📚 参考链接

- [RSSHub Twitter 路由文档](https://docs.rsshub.app/routes/social-media#twitter)
- [RSSHub 部署配置文档](https://docs.rsshub.app/deploy)
- [Twitter Cookie 获取教程](https://www.google.com/search?q=get+twitter+cookie+from+browser)

---

## ✅ 快速检查清单

配置完成后，请确认以下各项：

- [ ] 已从浏览器复制完整的 Twitter Cookie
- [ ] 已将 Cookie 填入 `docker-compose.yml` 的 `TWITTER_COOKIE` 环境变量
- [ ] Cookie 包含 `auth_token` 字段
- [ ] 已执行 `docker compose restart rsshub`
- [ ] RSSHub 容器正常运行 (`docker ps | grep rsshub`)
- [ ] 运行 `python3 rss_collector.py` 后 Twitter 源显示 ✅

全部完成？恭喜！🎉 你的 AI 每日报告现在可以订阅 Twitter 高价值源了！
