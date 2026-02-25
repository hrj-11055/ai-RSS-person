"""
云发布器模块

处理通过 SFTP、HTTP 或 FTP 将报告上传到云服务器。

Author: AI-RSS-PERSON Team
Version: 2.0.0
"""

import logging
from typing import Optional
from pathlib import Path

# Import shared utilities
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.utils import setup_logger, get_optional_env
from core.utils.constants import (
    DEFAULT_CLOUD_SERVER_HOST,
    DEFAULT_CLOUD_SERVER_PORT,
    DEFAULT_CLOUD_SERVER_USER,
    DEFAULT_CLOUD_SERVER_REMOTE_PATH,
    DEFAULT_CLOUD_SERVER_JSON_REMOTE_PATH,
    DEFAULT_UPLOAD_METHOD,
    UPLOAD_METHOD_SFTP,
    UPLOAD_METHOD_HTTP,
    UPLOAD_METHOD_FTP,
)

# Configuration
CLOUD_SERVER_HOST = get_optional_env("CLOUD_SERVER_HOST", DEFAULT_CLOUD_SERVER_HOST)
CLOUD_SERVER_PORT = int(get_optional_env("CLOUD_SERVER_PORT", DEFAULT_CLOUD_SERVER_PORT))
CLOUD_SERVER_USER = get_optional_env("CLOUD_SERVER_USER", DEFAULT_CLOUD_SERVER_USER)
CLOUD_SERVER_PASSWORD = get_optional_env("CLOUD_SERVER_PASSWORD", "")
CLOUD_SERVER_KEY_PATH = get_optional_env("CLOUD_SERVER_KEY_PATH", "")
CLOUD_SERVER_REMOTE_PATH = get_optional_env("CLOUD_SERVER_REMOTE_PATH", DEFAULT_CLOUD_SERVER_REMOTE_PATH)
CLOUD_SERVER_JSON_REMOTE_PATH = get_optional_env("CLOUD_SERVER_JSON_REMOTE_PATH", DEFAULT_CLOUD_SERVER_JSON_REMOTE_PATH)
UPLOAD_METHOD = get_optional_env("UPLOAD_METHOD", DEFAULT_UPLOAD_METHOD)
HTTP_UPLOAD_URL = get_optional_env("HTTP_UPLOAD_URL", "")
HTTP_UPLOAD_TOKEN = get_optional_env("HTTP_UPLOAD_TOKEN", "")

# Setup logger
logger = setup_logger(__name__, get_optional_env("LOG_LEVEL", "INFO"))


class CloudPublisher:
    """
    云文件上传器，支持 SFTP、HTTP 和 FTP 协议。

    示例：
        >>> publisher = CloudPublisher()
        >>> success = publisher.upload("report.html", "report.html")
        >>> if success:
        ...     print("Upload successful!")
    """

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        key_path: Optional[str] = None,
        remote_path: Optional[str] = None,
        method: Optional[str] = None
    ):
        """
        初始化云发布器。

        参数：
            host: 服务器主机名（默认为 CLOUD_SERVER_HOST 环境变量）
            port: 服务器端口（默认为 CLOUD_SERVER_PORT 环境变量）
            user: 用户名（默认为 CLOUD_SERVER_USER 环境变量）
            password: 密码（默认为 CLOUD_SERVER_PASSWORD 环境变量）
            key_path: SSH 私钥路径（默认为 CLOUD_SERVER_KEY_PATH 环境变量）
            remote_path: 默认远程路径（默认为 CLOUD_SERVER_REMOTE_PATH 环境变量）
            method: 上传方式：sftp、http 或 ftp（默认为 UPLOAD_METHOD 环境变量）
        """
        self.host = host or CLOUD_SERVER_HOST
        self.port = port if port is not None else CLOUD_SERVER_PORT
        self.user = user or CLOUD_SERVER_USER
        self.password = password or CLOUD_SERVER_PASSWORD
        self.key_path = key_path or CLOUD_SERVER_KEY_PATH
        self.remote_path = remote_path or CLOUD_SERVER_REMOTE_PATH
        self.method = method or UPLOAD_METHOD

        # HTTP-specific config
        self.http_upload_url = HTTP_UPLOAD_URL
        self.http_upload_token = HTTP_UPLOAD_TOKEN

    def upload(
        self,
        local_file: str,
        remote_filename: str,
        remote_path: Optional[str] = None
    ) -> bool:
        """
        使用配置的方式上传文件到云服务器。

        参数：
            local_file: 本地文件路径
            remote_filename: 远程文件名
            remote_path: 可选的远程路径（未提供则使用默认路径）

        返回：
            上传成功返回 True，否则返回 False

        示例：
            >>> publisher = CloudPublisher()
            >>> success = publisher.upload("report.html", "report.html")
        """
        logger.info(f"☁️ 开始上传文件: {local_file}")

        target_path = remote_path if remote_path else self.remote_path

        if self.method == UPLOAD_METHOD_SFTP:
            return self._upload_via_sftp(local_file, remote_filename, target_path)
        elif self.method == UPLOAD_METHOD_HTTP:
            return self._upload_via_http(local_file, remote_filename)
        elif self.method == UPLOAD_METHOD_FTP:
            return self._upload_via_ftp(local_file, remote_filename, target_path)
        else:
            logger.error(f"❌ 不支持的上传方式: {self.method}")
            return False

    def _upload_via_sftp(
        self,
        local_file: str,
        remote_filename: str,
        remote_path: str
    ) -> bool:
        """
        Upload file via SFTP.

        Args:
            local_file: Path to local file
            remote_filename: Name for the remote file
            remote_path: Remote directory path

        Returns:
            True if succeeded, False otherwise
        """
        if not self.host or not self.user:
            logger.error("❌ SFTP上传缺少 CLOUD_SERVER_HOST 或 CLOUD_SERVER_USER 配置")
            return False

        try:
            import paramiko
        except ImportError:
            logger.error("❌ 未安装 paramiko 库，请运行: pip install paramiko")
            return False

        try:
            # Create SSH client
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            # Connect (prefer SSH key, fallback to password)
            if self.key_path and Path(self.key_path).exists():
                logger.info(f"🔑 使用SSH密钥连接: {self.key_path}")
                key = paramiko.RSAKey.from_private_key_file(self.key_path)
                ssh.connect(self.host, port=self.port, username=self.user, pkey=key, timeout=60)
            elif self.password:
                logger.info(f"🔐 使用密码连接服务器")
                ssh.connect(self.host, port=self.port, username=self.user, password=self.password, timeout=60)
            else:
                logger.error("❌ 未配置SSH密钥或密码")
                return False

            # Create SFTP client
            sftp = ssh.open_sftp()

            # Ensure remote directory exists
            self._ensure_remote_directory(sftp, remote_path)

            # Upload file
            remote_file = f"{remote_path}/{remote_filename}"
            logger.info(f"📤 正在上传到 {self.host}:{remote_file}")
            sftp.put(local_file, remote_file)

            # Close connections
            sftp.close()
            ssh.close()

            logger.info(f"✅ 文件上传成功: {remote_file}")
            return True

        except paramiko.AuthenticationException:
            logger.error("❌ 认证失败：请检查用户名、密码或SSH密钥")
            return False
        except paramiko.SSHException as e:
            logger.error(f"❌ SSH连接错误: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ SFTP上传失败: {e}")
            return False

    def _upload_via_http(self, local_file: str, remote_filename: str) -> bool:
        """
        Upload file via HTTP POST.

        Args:
            local_file: Path to local file
            remote_filename: Name for the remote file

        Returns:
            True if succeeded, False otherwise
        """
        if not self.http_upload_url:
            logger.error("❌ 未配置HTTP_UPLOAD_URL")
            return False

        try:
            import requests
        except ImportError:
            logger.error("❌ 未安装 requests 库")
            return False

        try:
            logger.info(f"📤 正在通过HTTP上传到: {self.http_upload_url}")

            # Prepare file and data
            with open(local_file, 'rb') as f:
                files = {'file': (remote_filename, f, 'text/html')}

                # Add auth header if token configured
                headers = {}
                if self.http_upload_token:
                    headers['Authorization'] = f'Bearer {self.http_upload_token}'

                # Send POST request
                response = requests.post(self.http_upload_url, files=files, headers=headers, timeout=120)

                if response.status_code == 200:
                    logger.info(f"✅ HTTP上传成功: {response.text}")
                    return True
                else:
                    logger.error(f"❌ HTTP上传失败: {response.status_code} - {response.text}")
                    return False

        except Exception as e:
            logger.error(f"❌ HTTP上传异常: {e}")
            return False

    def _upload_via_ftp(
        self,
        local_file: str,
        remote_filename: str,
        remote_path: str
    ) -> bool:
        """
        Upload file via FTP.

        Args:
            local_file: Path to local file
            remote_filename: Name for the remote file
            remote_path: Remote directory path

        Returns:
            True if succeeded, False otherwise
        """
        if not self.host or not self.user:
            logger.error("❌ FTP上传缺少 CLOUD_SERVER_HOST 或 CLOUD_SERVER_USER 配置")
            return False

        try:
            from ftplib import FTP
        except ImportError:
            logger.error("❌ Python标准库中应该包含ftplib，但导入失败")
            return False

        try:
            logger.info(f"📤 正在通过FTP上传到 {self.host}")

            # Connect to FTP server
            ftp = FTP()
            ftp_port = self.port if self.port != 22 else 21  # Default FTP port
            ftp.connect(self.host, port=ftp_port, timeout=60)
            ftp.login(self.user, self.password)

            # Change to remote directory
            try:
                ftp.cwd(remote_path)
            except Exception:
                logger.warning(f"⚠️ 远程目录不存在，尝试创建: {remote_path}")
                try:
                    ftp.mkd(remote_path)
                    ftp.cwd(remote_path)
                except Exception as e:
                    logger.error(f"❌ 无法创建远程目录: {e}")
                    ftp.quit()
                    return False

            # Upload file
            with open(local_file, 'rb') as f:
                ftp.storbinary(f'STOR {remote_filename}', f)

            ftp.quit()
            logger.info(f"✅ FTP上传成功: {remote_filename}")
            return True

        except Exception as e:
            logger.error(f"❌ FTP上传失败: {e}")
            return False

    def _ensure_remote_directory(self, sftp, remote_path: str):
        """
        Ensure remote directory exists, create if needed.

        Args:
            sftp: Paramiko SFTP client
            remote_path: Remote directory path
        """
        try:
            sftp.stat(remote_path)
        except IOError:
            logger.warning(f"⚠️ 远程目录不存在，尝试创建: {remote_path}")

            # Try to create directory recursively
            dirs = []
            dir_path = remote_path
            while dir_path != '/':
                try:
                    sftp.stat(dir_path)
                    break
                except IOError:
                    dirs.append(dir_path)
                    dir_path = str(Path(dir_path).parent)

            # Create directories in reverse order
            for dir_path in reversed(dirs):
                try:
                    sftp.mkdir(dir_path)
                    logger.info(f"✅ 创建远程目录: {dir_path}")
                except IOError:
                    pass  # Directory might already exist


if __name__ == "__main__":
    # Test mode
    print("🧪 Cloud Publisher Test Mode")
    print("=" * 50)

    publisher = CloudPublisher()

    print(f"Host: {publisher.host}")
    print(f"Port: {publisher.port}")
    print(f"User: {publisher.user}")
    print(f"Method: {publisher.method}")
    print(f"Key Path: {publisher.key_path or 'Not configured'}")
    print(f"Remote Path: {publisher.remote_path}")
    print()
    print("To test upload, run:")
    print('  python -c "from lib.publishers.cloud_publisher import CloudPublisher; publisher = CloudPublisher(); publisher.upload(\'test.html\', \'test.html\')"')
