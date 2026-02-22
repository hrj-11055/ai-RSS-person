# 重新发送报告到邮箱

## 概述

如果需要重新发送某天的日报到邮箱，可以使用 `send_report.sh` 脚本。

## 使用方法

### 方式 1：发送指定日期的报告

```bash
./send_report.sh reports/2026-02-15.md
```

### 方式 2：发送今天的报告

```bash
# 获取今天的日期
TODAY=$(date "+%Y-%m-%d")
./send_report.sh reports/${TODAY}.md
```

### 方式 3：发送最新的报告

```bash
# 自动查找最新日期的报告
./send_report.sh reports/$(ls -t reports/*.md | head -1 | awk '{print $NF}')
```

## 功能说明

脚本会：
1. 读取指定的 Markdown 文件
2. 将 Markdown 转换为 HTML 格式
3. 发送邮件到配置的收件人
4. Markdown 文件作为附件

## 邮件配置

邮件配置来自 `[.env](.env)`：

```bash
# SMTP 服务器
SMTP_SERVER=smtp.qq.com

# 发件人
SENDER_EMAIL=1415994589@qq.com

# 收件人
RECEIVER_EMAIL=ainfo@aicoming.cn

# 抄送（可选）
CC_EMAIL=
BCC_EMAIL=
```

## 示例

```bash
# 发送 2 月 15 日的报告
./send_report.sh reports/2026-02-15.md
```

**输出**：
```
📧 正在发送报告...
文件: reports/2026-02-15.md
邮件主题: 📊 AI 日报 - 2026-02-15

📧 正在连接SMTP服务器: smtp.qq.com:465
✅ 邮件发送成功！
📮 收件人: ainfo@aicoming.cn
✅ 邮件发送成功！

✅ 完成
```

## 相关文件

- **[send_report.sh](send_report.sh)** - 重新发送脚本
- **[email_sender.py](email_sender.py)** - 邮件发送模块
- **[.env](.env)** - 邮件配置
