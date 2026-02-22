# SSH 连接问题修复说明

## 问题描述

定时任务运行时出现 SSH 连接超时错误：
```
❌ SSH连接错误: Timeout opening channel.
```

## 原因

SSH 连接超时时间设置为 30 秒，在网络较慢或服务器响应较慢时会导致超时。

## 解决方案

已将所有超时时间从 30 秒增加到 60/120 秒：

| 连接类型 | 原超时 | 新超时 |
|---------|--------|--------|
| SSH 连接 | 30s | **60s** |
| FTP 连接 | 30s | **60s** |
| HTTP 上传 | 60s | **120s** |

## 修改的文件

**[lib/publishers/cloud_publisher.py](lib/publishers/cloud_publisher.py)**:
- 第 159 行：SSH 密钥连接超时
- 第 162 行：SSH 密码连接超时
- 第 229 行：HTTP 上传超时
- 第 271 行：FTP 连接超时

## 测试结果

```
✅ 上传结果: 成功
```

## 建议

1. **网络稳定时**：30 秒超时足够
2. **使用移动网络**：建议增加到 60 秒
3. **服务器响应慢**：可能需要更长超时

## 相关配置

**[.env](.env)** 环境变量：
```bash
# 服务器配置
CLOUD_SERVER_HOST=8.135.37.159
CLOUD_SERVER_PORT=22
CLOUD_SERVER_USER=root
CLOUD_SERVER_KEY_PATH=/Users/MarkHuang/.ssh/id_rsa
CLOUD_SERVER_REMOTE_PATH=/var/www/html/reports
UPLOAD_METHOD=sftp

# JSON 文件路径
CLOUD_SERVER_JSON_REMOTE_PATH=/var/www/json/report
```
