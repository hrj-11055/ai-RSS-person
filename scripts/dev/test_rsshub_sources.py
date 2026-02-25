#!/usr/bin/env python3
"""
测试 RSSHub 源状态（npm/systemd/pm2 部署方式）
"""

import requests

RSSHUB_URL = "http://localhost:1200"


def test_rsshub_health():
    print("=" * 60)
    print("🧪 RSSHub 诊断（npm版）")
    print("=" * 60)

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
            elif response.status_code in {401, 403, 429, 503}:
                print("   ⚠️  可能是 Twitter 认证失效或限流")
            else:
                print(f"   ⚠️  状态码: {response.status_code}")
        except Exception as e:
            print(f"\n   {desc} ({route})")
            print(f"   ❌ 请求失败: {str(e)}")

    print("\n" + "=" * 60)
    print("💡 若 Twitter 路由异常：")
    print("   1. 运行: bash scripts/dev/update_twitter_cookie.sh")
    print("   2. 确认 .env 中 RSSHUB_RESTART_CMD 或 RSSHUB_SERVICE_NAME 已配置")
    print("   3. 重试本脚本")


if __name__ == "__main__":
    test_rsshub_health()
