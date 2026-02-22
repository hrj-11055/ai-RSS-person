#!/usr/bin/env python3
"""
测试上传实际的报告文件到云服务器
"""
import paramiko
import sys
from pathlib import Path
from dotenv import load_dotenv
import os

# 加载环境变量
load_dotenv()

# 服务器配置
HOST = os.getenv("CLOUD_SERVER_HOST", "8.135.37.159")
PORT = int(os.getenv("CLOUD_SERVER_PORT", "22"))
USER = os.getenv("CLOUD_SERVER_USER", "root")
KEY_PATH = os.getenv("CLOUD_SERVER_KEY_PATH", "/Users/MarkHuang/.ssh/id_rsa")
REMOTE_PATH = os.getenv("CLOUD_SERVER_REMOTE_PATH", "/var/www/html/reports")

def upload_report_file(local_file_path):
    """上传报告文件到服务器"""
    print("🔧 测试SFTP上传...")
    print(f"   主机: {HOST}:{PORT}")
    print(f"   用户: {USER}")
    print(f"   密钥: {KEY_PATH}")
    print(f"   远程目录: {REMOTE_PATH}")
    print(f"   本地文件: {local_file_path}")
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
            print(f"⚠️  远程目录不存在，尝试创建: {REMOTE_PATH}")
            sftp.mkdir(REMOTE_PATH)
            print(f"✅ 创建目录成功: {REMOTE_PATH}")

        # 获取文件名
        filename = Path(local_file_path).name
        remote_file = f"{REMOTE_PATH}/{filename}"

        # 上传文件
        print(f"📤 正在上传文件...")
        print(f"   {local_file_path}")
        print(f"   → {remote_file}")
        sftp.put(local_file_path, remote_file)

        # 获取文件大小
        file_size = Path(local_file_path).stat().st_size
        print(f"✅ 文件上传成功！大小: {file_size:,} bytes ({file_size/1024:.1f} KB)")

        # 验证文件
        try:
            remote_stat = sftp.stat(remote_file)
            print(f"✅ 文件验证成功！远程文件大小: {remote_stat.st_size:,} bytes")

            # 生成访问URL
            print(f"\n🌐 访问地址:")
            print(f"   http://{HOST}/reports/{filename}")
        except IOError:
            print("❌ 文件验证失败")

        # 清理
        sftp.close()
        ssh.close()
        print("\n✅ 上传测试完成！")

        return True

    except paramiko.AuthenticationException:
        print("❌ 认证失败：请检查SSH密钥配置")
        return False
    except paramiko.SSHException as e:
        print(f"❌ SSH错误: {e}")
        return False
    except FileNotFoundError:
        print(f"❌ 本地文件不存在: {local_file_path}")
        return False
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("="*60)
    print("测试上传实际报告文件")
    print("="*60)
    print()

    # 查找最新的HTML报告
    reports_dir = Path("reports")
    if not reports_dir.exists():
        print("❌ reports 目录不存在")
        sys.exit(1)

    # 获取所有HTML文件
    html_files = list(reports_dir.glob("*.html"))

    if not html_files:
        print("❌ reports 目录中没有HTML文件")
        sys.exit(1)

    # 按修改时间排序，获取最新的
    html_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    latest_file = html_files[0]

    print(f"📁 找到 {len(html_files)} 个HTML文件")
    print(f"📄 最新文件: {latest_file.name}")
    print(f"   修改时间: {latest_file.stat().st_mtime}")
    print()

    # 上传最新的文件
    success = upload_report_file(str(latest_file))

    sys.exit(0 if success else 1)
