#!/usr/bin/env python3
"""
测试 RSSHub 源状态

诊断 RSSHub Twitter 配置问题，并提供解决方案。
"""

import requests
import json

RSSHUB_URL = "http://localhost:1200"

def test_rsshub_health():
    """测试 RSSHub 健康状态"""
    print("=" * 60)
    print("🧪 RSSHub 诊断")
    print("=" * 60)

    # 健康检查
    print("\n1️⃣ 健康检查...")
    try:
        response = requests.get(f"{RSSHUB_URL}/healthz", timeout=5)
        if response.status_code == 200:
            print("✅ RSSHub 服务正常运行")
        else:
            print(f"❌ RSSHub 状态异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 连接失败: {str(e)}")
        return False

    # 测试不同的路由
    print("\n2️⃣ 测试路由...")

    test_routes = [
        ("/", "首页"),
        ("/api/routes", "API 路由列表"),
        ("/twitter/user/OpenAI", "Twitter 源"),
    ]

    for route, desc in test_routes:
        try:
            response = requests.get(f"{RSSHUB_URL}{route}", timeout=10)
            print(f"\n   {desc} ({route})")
            print(f"   状态码: {response.status_code}")

            if response.status_code == 200:
                print("   ✅ 正常")
            elif response.status_code == 503:
                # 尝试解析错误信息
                if "ConfigNotFoundError" in response.text:
                    print("   ❌ 配置错误: Twitter API 未配置或 Cookie 过期")
                elif "NotFoundError" in response.text:
                    print("   ❌ 路由不存在")
                else:
                    print("   ❌ 服务不可用")
            else:
                print(f"   ⚠️  状态码: {response.status_code}")

        except Exception as e:
            print(f"\n   {desc} ({route})")
            print(f"   ❌ 请求失败: {str(e)}")

    # 诊断和解决方案
    print("\n" + "=" * 60)
    print("🔍 诊断结果")
    print("=" * 60)

    print("\n💡 如果 Twitter 源显示配置错误：")
    print("   1. Twitter Cookie 可能已过期（有效期 1-2 周）")
    print("   2. 需要更新 docker-compose.yml 中的 TWITTER_COOKIE")
    print("   3. 更新后需要重启 Docker 容器")

    print("\n📝 更新 Twitter Cookie 步骤：")
    print("   1. 打开浏览器，访问 https://twitter.com")
    print("   2. 按 F12 打开开发者工具")
    print("   3. 切换到 Network 标签")
    print("   4. 刷新页面，找到任意请求")
    print("   5. 查看 Request Headers 中的 cookie 字段")
    print("   6. 复制完整 cookie 值（包含 auth_token, ct0 等）")
    print("   7. 更新 docker-compose.yml 中的 TWITTER_COOKIE")
    print("   8. 重启容器：docker-compose restart rsshub")

    print("\n🔄 重启 RSSHub 容器命令：")
    print("   docker restart rss-person-rsshub")
    print("   或")
    print("   docker-compose restart rsshub")

    print("\n" + "=" * 60)
    print("📋 当前 RSSHub 容器状态")
    print("=" * 60)

    import subprocess
    try:
        result = subprocess.run(
            ["docker", "ps", "--filter", "name=rss-person-rsshub", "--format", "table {{.Names}}\t{{.Status}}\t{{.Ports}}"],
            capture_output=True,
            text=True
        )
        print(result.stdout)
    except Exception as e:
        print(f"❌ 无法获取容器状态: {str(e)}")


if __name__ == "__main__":
    test_rsshub_health()
