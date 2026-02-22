# Mac 定时任务快速指南

## 🚀 快速开始

### 1️⃣ 安装定时任务

```bash
./manage_cron.sh install
```

**这会：**
- ✅ 将配置文件安装到 `~/Library/LaunchAgents/`
- ✅ 设置每天早上 9:00 自动运行
- ✅ 自动保存日志到 `logs/` 目录
- ✅ 完成后自动发送邮件

### 2️⃣ 查看任务状态

```bash
./manage_cron.sh status
```

### 3️⃣ 手动测试运行

```bash
./manage_cron.sh test
```

### 4️⃣ 查看运行日志

```bash
./manage_cron.sh logs
```

### 5️⃣ 卸载定时任务

```bash
./manage_cron.sh uninstall
```

---

## 📋 完整工作流程

**每天 9:00 AM 自动执行：**

```
① 收集 RSS 文章（58+ 源）
② 双重评分排序（源权威性 60% + 内容相关性 40%）
③ AI 分析（DeepSeek API）
④ 生成 Markdown 报告 → 保存本地 (reports/YYYY-MM-DD.md)
⑤ 生成 JSON 数据 → 上传云服务器
⑥ 转换 JSON 为 Markdown → 发送邮件
```

**输出文件：**
- `reports/YYYY-MM-DD.md` - Markdown 报告（本地保存）
- `reports/YYYY-MM-DD.json` - JSON 数据（上传云服务器）
- 邮件附件：`YYYY-MM-DD.md`

---

## ⚙️ 修改运行时间

如果你想修改运行时间：

```bash
./manage_cron.sh edit
```

找到这一行：
```xml
<key>StartCalendarInterval</key>
<dict>
    <key>Hour</key>
    <integer>9</integer>    <!-- 修改这里：0-23 -->
    <key>Minute</key>
    <integer>0</integer>    <!-- 修改这里：0-59 -->
</dict>
```

**示例：**
- `Hour: 9, Minute: 0` - 每天早上9点
- `Hour: 20, Minute: 30` - 每天晚上8:30
- `Hour: 6, Minute: 0` - 每天早上6点

修改后需要重新安装：
```bash
./manage_cron.sh uninstall
./manage_cron.sh install
```

---

## ⚠️ 重要提示

### 1. Mac 必须开机/唤醒

Mac 需要在定时时间点**处于开机状态**：

**推荐设置：**
- ✅ **禁止 Mac 自动休眠**（系统设置 → 电池 → 选项 → 防止自动睡眠）
- ✅ 或者设置**定时唤醒**（系统偏好设置 → 节能 → 计划）

### 2. 设置计划开机/唤醒

**macOS Ventura (13.0+)：**
```bash
系统设置 → 电池 → 计划
# 设置每天早上 7:55 唤醒（留5分钟缓冲）
```

**macOS Monterey (12.0) 及更早：**
```bash
系统偏好设置 → 节能 → 计划
# 设置启动或唤醒时间
```

### 3. 检查任务是否运行

运行日志会保存在：
```
logs/stdout.log  - 标准输出
logs/stderr.log  - 错误输出
```

查看最近运行：
```bash
tail -50 logs/stdout.log
```

---

## 📊 监控运行状态

### 查看系统日志

```bash
# 查看 launchd 日志
log show --predicate 'process == "Python"' --last 1h

# 或使用 Console.app
open /Applications/Utilities/Console.app
```

### 测试是否正常工作

```bash
# 1. 手动运行一次
./manage_cron.sh test

# 2. 检查是否成功生成报告
ls -lh reports/ | tail -5

# 3. 查看日志
./manage_cron.sh logs

# 4. 测试邮件发送（需要先生成报告）
./manage_cron.sh test-email
```

---

## 🔧 故障排查

### 问题1：任务没有运行

**检查：**
```bash
# 1. 检查任务是否加载
./manage_cron.sh status

# 2. 检查日志
./manage_cron.sh logs

# 3. 手动测试
./manage_cron.sh test
```

**常见原因：**
- Mac 在定时时间处于休眠状态
- Python 路径不正确
- .env 文件配置错误

### 问题2：报告没有上传到服务器

**检查：**
```bash
# 1. 测试 SSH 连接
ssh root@8.135.37.159

# 2. 测试 SFTP 上传
python test_upload.py

# 3. 检查 .env 配置
cat .env | grep CLOUD_SERVER
```

### 问题3：邮件发送失败

**检查：**
```bash
# 1. 检查 .env 邮件配置
cat .env | grep EMAIL_

# 2. 测试邮件发送
./manage_cron.sh test-email

# 3. 查看错误日志
cat logs/stderr.log | tail -20
```

**常见原因：**
- SMTP 服务器配置错误
- 邮箱密码或授权码错误
- 网络连接问题

### 问题4：Python 找不到模块

**解决：**
```bash
# 确保在正确的环境中运行
pip3 list | grep -E "feedparser|openai|paramiko"

# 如果缺少，重新安装
pip3 install feedparser openai python-dotenv paramiko
```

---

## 💡 使用建议

### 1. 试运行期间

- ✅ 每天早上手动检查报告是否生成
- ✅ 定期查看日志：`./manage_cron.sh logs`
- ✅ 验证上传到服务器：访问 `http://8.135.37.159/reports/`
- ✅ 检查邮件是否正常接收

### 2. 监控费用

- DeepSeek API 费用：每次约 ¥0.15-0.30
- 每天运行 1 次，月费用约：¥5-10
- 查看费用统计：在日志中搜索 "本次消耗"

### 3. 优化建议

如果发现某些时间点 Mac 经常休眠，可以：
1. 调整运行时间到更合适的时间
2. 设置 Mac 自动唤醒
3. 或者改用手动运行

---

## 📅 环境配置要求

### 必需配置

在 `.env` 文件中配置：

```bash
# DeepSeek API（必需）
DEEPSEEK_API_KEY=sk-xxxxx

# 云服务器上传（必需）
CLOUD_SERVER_HOST=8.135.37.159
CLOUD_SERVER_PORT=22
CLOUD_SERVER_USER=root
CLOUD_SERVER_KEY_PATH=/path/to/ssh/key
# 或使用密码
CLOUD_SERVER_PASSWORD=your_password

# 邮件发送（必需）
EMAIL_SMTP_HOST=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_FROM=your@gmail.com
EMAIL_PASSWORD=your_app_password
EMAIL_TO=recipient@example.com
```

---

## 🎯 现在就可以开始！

```bash
# 1. 确认 .env 配置正确
cat .env

# 2. 安装定时任务
./manage_cron.sh install

# 3. 手动测试一次
./manage_cron.sh test

# 4. 查看结果
ls -lh reports/
./manage_cron.sh logs

# 5. 测试邮件发送
./manage_cron.sh test-email
```

**明天早上 9:00 就会自动运行了！** 🎉

---

## 📝 管理命令速查

```bash
./manage_cron.sh install    # 安装定时任务
./manage_cron.sh uninstall  # 卸载定时任务
./manage_cron.sh status     # 查看任务状态
./manage_cron.sh logs       # 查看运行日志
./manage_cron.sh test       # 手动运行完整流程
./manage_cron.sh test-email # 测试邮件发送
./manage_cron.sh edit       # 编辑定时配置
```
