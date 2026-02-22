# daily_report_PRO_cloud.py 使用指南

## 📋 简介

`daily_report_PRO_cloud.py` 是基于 `daily_report_PRO_wechat.py` 的云服务器版本，主要特点：

- ✅ **移除微信公众号功能**：不需要配置微信相关参数
- ✅ **支持云服务器自动上传**：生成的报告自动上传到云服务器
- ✅ **多种上传方式**：支持 SFTP、HTTP、FTP 三种上传方式
- ✅ **完整的HTML报告**：保留所有核心功能（RSS采集、AI分析、智能排序）

---

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install paramiko>=2.11.0
# 或更新所有依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env`（如果还没有）：

```bash
cp .env.example .env
```

编辑 `.env` 文件，添加以下配置：

```bash
# 必需配置
DEEPSEEK_API_KEY=sk-xxxxx  # DeepSeek API密钥

# 云服务器配置（必需）
CLOUD_SERVER_HOST=8.135.37.159 （你的服务器IP地址）
CLOUD_SERVER_PORT=22
CLOUD_SERVER_USER=root

# 认证方式（二选一）
CLOUD_SERVER_PASSWORD=your_ssh_password
# 或使用SSH密钥（推荐）
CLOUD_SERVER_KEY_PATH=/path/to/your/private/key

# 远程路径
CLOUD_SERVER_REMOTE_PATH=/var/www/html/reports

# 上传方式
UPLOAD_METHOD=sftp
```

### 3. 运行程序

```bash
python daily_report_PRO_cloud.py
```

程序会自动：
1. 采集过去24小时的RSS资讯
2. 使用AI进行分析和生成报告
3. 保存JSON报告到本地 `reports/` 目录
4. 自动上传报告到云服务器
5. md报告发送到个人邮箱

---

## ⚙️ 配置详解

### 云服务器配置

| 配置项 | 说明 | 默认值 | 必需 |
|--------|------|--------|------|
| `CLOUD_SERVER_HOST` | 服务器IP地址或域名 | `8.135.37.159` | ✅ |
| `CLOUD_SERVER_PORT` | SSH端口 | `22` | ✅ |
| `CLOUD_SERVER_USER` | SSH用户名 | `root` | ✅ |
| `CLOUD_SERVER_PASSWORD` | SSH密码 | - | 密码登录时必需 |
| `CLOUD_SERVER_KEY_PATH` | SSH私钥路径 | - | 密钥登录时必需 |
| `CLOUD_SERVER_REMOTE_PATH` | 远程保存路径 | `/var/www/html/reports` | ✅ |
| `UPLOAD_METHOD` | 上传方式 | `sftp` | ✅ |

### 上传方式

程序支持三种上传方式：

#### 1. SFTP（推荐）

**优点：**
- 安全性高，使用SSH加密
- 支持大文件传输
- 可靠性好

**配置：**
```bash
UPLOAD_METHOD=sftp
CLOUD_SERVER_HOST=8.135.37.159
CLOUD_SERVER_PORT=22
CLOUD_SERVER_USER=root

# 方式1：使用密码
CLOUD_SERVER_PASSWORD=your_password

# 方式2：使用SSH密钥（推荐）
CLOUD_SERVER_KEY_PATH=/home/user/.ssh/id_rsa
```

**服务器要求：**
- 需要安装并运行 SSH 服务
- 密码登录：确保服务器允许密码认证
- 密钥登录：需要配置公钥到服务器的 `~/.ssh/authorized_keys`

#### 2. HTTP

**优点：**
- 配置简单
- 不需要SSH访问权限

**缺点：**
- 需要在服务器端部署接收接口
- 安全性依赖于HTTPS

**配置：**
```bash
UPLOAD_METHOD=http
HTTP_UPLOAD_URL=http://8.135.37.159/api/upload
HTTP_UPLOAD_TOKEN=your_secret_token
```

**服务器接口示例（Python Flask）：**
```python
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/api/upload', methods=['POST'])
def upload_file():
    # 验证token
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if token != 'your_secret_token':
        return jsonify({'error': 'Unauthorized'}), 401

    # 保存文件
    file = request.files.get('file')
    if file:
        filename = file.filename
        file.save(f'/var/www/html/reports/{filename}')
        return jsonify({'success': True, 'filename': filename})

    return jsonify({'error': 'No file provided'}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

#### 3. FTP

**优点：**
- 广泛支持
- 简单易用

**缺点：**
- 明文传输（不安全）
- 大多数云服务器默认不开启

**配置：**
```bash
UPLOAD_METHOD=ftp
CLOUD_SERVER_HOST=8.135.37.159
CLOUD_SERVER_PORT=21
CLOUD_SERVER_USER=ftpuser
CLOUD_SERVER_PASSWORD=ftp_password
```

---

## 🔐 SSH密钥配置（推荐）

### 生成SSH密钥对

在本地机器上生成SSH密钥：

```bash
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"
```

按提示操作：
- 保存路径：默认 `~/.ssh/id_rsa`
- 密码：可设置也可留空（直接回车）

### 配置服务器

将公钥上传到服务器：

```bash
# 方式1：使用 ssh-copy-id（推荐）
ssh-copy-id root@8.135.37.159

# 方式2：手动复制
cat ~/.ssh/id_rsa.pub | ssh root@8.135.37.159 'mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys'
```

### 配置程序

在 `.env` 文件中配置：

```bash
CLOUD_SERVER_KEY_PATH=/Users/yourname/.ssh/id_rsa
```

---

## 📊 程序输出示例

```
2026-02-05 08:00:00 - __main__ - INFO - 🚀 启动采集 (过去24小时) ...
2026-02-05 08:00:01 - __main__ - INFO - 📡 扫描: OpenAI Twitter ...
2026-02-05 08:00:02 - __main__ - INFO - ✅ OpenAI Twitter: 发现 5 条，入选 3 条 (24h内)
...
2026-02-05 08:05:00 - __main__ - INFO - 📊 采集完成: 共收集 45 篇文章
2026-02-05 08:05:01 - __main__ - INFO - 📊 开始智能排序 (共 45 条文章)...
2026-02-05 08:05:02 - __main__ - INFO - ✅ 排序完成，已筛选 Top 20 条
2026-02-05 08:05:03 - __main__ - INFO - 🤖 开始 AI 分析 (Top 20 条)...
...
2026-02-05 08:15:00 - __main__ - INFO - 💾 正在保存到本地文件...
2026-02-05 08:15:01 - __main__ - INFO - ✅ HTML 已保存到: reports/AI_Daily_2026-02-05.html
2026-02-05 08:15:02 - __main__ - INFO - ☁️ 正在上传到云服务器...
2026-02-05 08:15:02 - __main__ - INFO - 🔑 使用SSH密钥连接: /Users/yourname/.ssh/id_rsa
2026-02-05 08:15:03 - __main__ - INFO - 📤 正在上传到 8.135.37.159:/var/www/html/reports/AI_Daily_2026-02-05.html
2026-02-05 08:15:05 - __main__ - INFO - ✅ 文件上传成功: /var/www/html/reports/AI_Daily_2026-02-05.html
2026-02-05 08:15:05 - __main__ - INFO - ✅ 报告已成功上传到云服务器: 8.135.37.159:/var/www/html/reports/AI_Daily_2026-02-05.html
2026-02-05 08:15:05 - __main__ - INFO - 🌐 访问地址示例: http://8.135.37.159/reports/AI_Daily_2026-02-05.html
2026-02-05 08:15:05 - __main__ - INFO - 📊 本次消耗: 输入 50000 | 输出 10000 | 费用: ¥0.13000
```

---

## 🛠️ 故障排查

### 问题1：SSH连接失败

**错误信息：**
```
❌ 认证失败：请检查用户名、密码或SSH密钥
```

**解决方案：**
1. 检查服务器地址是否正确
2. 检查SSH端口是否正确（默认22）
3. 检查用户名和密码是否正确
4. 如果使用密钥，检查密钥路径是否正确
5. 测试SSH连接：`ssh root@8.135.37.159`

### 问题2：远程目录不存在

**错误信息：**
```
⚠️ 远程目录不存在，尝试创建: /var/www/html/reports
```

**解决方案：**
- 程序会自动尝试创建目录
- 如果失败，请手动在服务器上创建：
  ```bash
  ssh root@8.135.37.159
  mkdir -p /var/www/html/reports
  chmod 755 /var/www/html/reports
  ```

### 问题3：权限不足

**错误信息：**
```
❌ Permission denied
```

**解决方案：**
1. 确保SSH用户有写入远程目录的权限
2. 检查目录权限：
   ```bash
   ls -la /var/www/html/
   ```
3. 修改目录权限：
   ```bash
   chown -R www-data:www-data /var/www/html/reports
   chmod -R 755 /var/www/html/reports
   ```

### 问题4：paramiko 未安装

**错误信息：**
```
❌ 未安装 paramiko 库
```

**解决方案：**
```bash
pip install paramiko>=2.11.0
```

---

## 📝 与微信版本的对比

| 功能 | daily_report_PRO_wechat.py | daily_report_PRO_cloud.py |
|------|---------------------------|--------------------------|
| RSS采集 | ✅ | ✅ |
| AI分析 | ✅ | ✅ |
| 智能排序 | ✅ | ✅ |
| 本地保存 | ✅ | ✅ |
| 微信发布 | ✅ | ❌ |
| 云服务器上传 | ❌ | ✅ |
| 依赖要求 | wechatpy | paramiko |

---

## 🎯 最佳实践

### 1. 使用SSH密钥而非密码

- 更安全
- 无需在配置文件中明文存储密码
- 适合自动化脚本

### 2. 设置定时任务

使用 crontab 设置定时任务：

```bash
# 编辑 crontab
crontab -e

# 添加每天早上8点运行
0 8 * * * cd /path/to/RSS-person && python daily_report_PRO_cloud.py >> logs/cron.log 2>&1
```

### 3. 配置日志记录

在 `.env` 中设置日志级别：

```bash
LOG_LEVEL=INFO
```

对于调试，可以设置为 `DEBUG`：

```bash
LOG_LEVEL=DEBUG
```

### 4. 备份重要配置

备份 `.env` 文件（注意不要包含在版本控制中）：

```bash
cp .env .env.backup
```

---

## 🔗 相关链接

- [paramiko 文档](https://www.paramiko.org/)
- [SSH 密钥配置指南](https://www.ssh.com/academy/ssh/key)
- [服务器配置最佳实践](https://wiki.archlinux.org/title/SSH_keys)

---

## 📄 License

MIT
