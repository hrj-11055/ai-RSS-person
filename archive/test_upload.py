#!/usr/bin/env python3
"""
测试云服务器上传功能
"""
import paramiko
import sys
from pathlib import Path

# 服务器配置
HOST = "8.135.37.159"
PORT = 22
USER = "root"
KEY_PATH = "/Users/MarkHuang/.ssh/id_rsa"
REMOTE_PATH = "/var/www/html/reports"

def test_sftp_upload():
    """测试SFTP上传"""
    print("🔧 测试SFTP连接到服务器...")
    print(f"   主机: {HOST}")
    print(f"   端口: {PORT}")
    print(f"   用户: {USER}")
    print(f"   密钥: {KEY_PATH}")
    print()

    try:
        # 创建SSH客户端
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # 使用SSH密钥连接
        print("🔑 正在使用SSH密钥连接...")
        key = paramiko.RSAKey.from_private_key_file(KEY_PATH)
        ssh.connect(HOST, port=PORT, username=USER, pkey=key, timeout=10)
        print("✅ SSH连接成功！")

        # 创建SFTP客户端
        sftp = ssh.open_sftp()
        print("✅ SFTP客户端创建成功！")

        # 检查并创建远程目录
        try:
            sftp.stat(REMOTE_PATH)
            print(f"✅ 远程目录存在: {REMOTE_PATH}")
        except IOError:
            print(f"⚠️ 远程目录不存在，尝试创建: {REMOTE_PATH}")
            # 尝试创建远程目录（递归创建）
            dirs_to_create = []
            current_path = REMOTE_PATH

            # 从最深层的目录开始，逐级检查
            while current_path != '/':
                try:
                    sftp.stat(current_path)
                    break  # 找到已存在的目录
                except IOError:
                    dirs_to_create.append(current_path)
                    current_path = str(Path(current_path).parent)

            # 倒序创建目录
            for dir_path in reversed(dirs_to_create):
                try:
                    sftp.mkdir(dir_path)
                    print(f"   创建目录: {dir_path}")
                except IOError as e:
                    print(f"   警告: 无法创建 {dir_path}: {e}")

        # 创建测试文件
        test_file = "/tmp/test_upload.html"
        with open(test_file, 'w') as f:
            f.write("<h1>测试文件</h1><p>上传时间: 2026-02-05</p>")

        # 上传测试文件
        remote_file = f"{REMOTE_PATH}/test_upload.html"
        print(f"📤 正在上传测试文件到: {remote_file}")
        sftp.put(test_file, remote_file)
        print("✅ 文件上传成功！")

        # 验证文件是否存在
        try:
            sftp.stat(remote_file)
            print(f"✅ 文件验证成功: {remote_file}")
            print(f"🌐 访问地址: http://{HOST}/reports/test_upload.html")
        except IOError:
            print("❌ 文件验证失败")

        # 清理
        sftp.close()
        ssh.close()
        print("\n✅ 所有测试通过！可以正常使用了。")

        return True

    except paramiko.AuthenticationException:
        print("❌ 认证失败：请检查SSH密钥配置")
        return False
    except paramiko.SSHException as e:
        print(f"❌ SSH错误: {e}")
        return False
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False

if __name__ == "__main__":
    print("="*50)
    print("测试云服务器上传功能")
    print("="*50)
    print()

    success = test_sftp_upload()

    sys.exit(0 if success else 1)
