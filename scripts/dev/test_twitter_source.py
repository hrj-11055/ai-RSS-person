#!/usr/bin/env python3
"""
测试 Twitter 源是否正常工作

连接 RSSHub API → 访问 Twitter 路由 → 显示数据
"""

import requests
import feedparser
import sys
import os

# RSSHub 配置
RSSHUB_URL = "http://localhost:1200"
TWITTER_API_ROUTE = "/twitter/user/OpenAI"
AUTH_HEADER = {}  # Twitter 源不需要认证头（使用 RSSHub 配置中的 cookie）

def test_twitter_source():
    """测试 Twitter 源"""
    print("=" * 60)
    print("🧪 RSSHub Twitter 源测试")
    print("=" * 60)

    # 步骤 1: 检查 RSSHub 服务
    print("\n1️⃣ 检查 RSSHub 服务...")
    try:
        response = requests.get(f"{RSSHUB_URL}/healthz", timeout=5)
        if response.status_code == 200:
            print("✅ RSSHub 服务正常运行")
        else:
            print(f"❌ RSSHub 服务异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 连接失败: {str(e)}")
        return False

    # 步骤 2: 访问 Twitter 源数据
    print("\n2️⃣ 访问 Twitter 源数据...")
    try:
        # 使用默认的 guest token (如果需要，可以从 RSSHub Web 界面获取)
        response = requests.get(
            f"{RSSHUB_URL}{TWITTER_API_ROUTE}",
            headers=AUTH_HEADER,
            timeout=10
        )

        print(f"   状态码: {response.status_code}")

        if response.status_code == 200:
            print("✅ API 请求成功")

            # 尝试解析 RSS (XML 格式)
            try:
                feed = feedparser.parse(response.text)

                # 检查数据结构
                if feed.entries:
                    entries = feed.entries
                    print(f"✅ 数据格式正确: RSS feed")
                    print(f"📊 Tweet 数量: {len(entries)}")

                    # 显示前 3 条
                    if len(entries) > 0:
                        print("\n📋 最新 3 条 Tweet:")
                        for i, entry in enumerate(entries[:3], 1):
                            title = entry.get('title', 'N/A')
                            link = entry.get('link', 'N/A')
                            published = entry.get('published', 'N/A')
                            print(f"   [{i}] {published[:19] if published != 'N/A' else 'N/A'}")
                            print(f"      标题: {title[:70]}...")
                            print(f"      链接: {link}")
                else:
                    print("⚠️  响应格式异常")
                    print(f"   Feed 条目数: {len(feed.entries) if hasattr(feed, 'entries') else 0}")

            except Exception as e:
                print(f"❌ RSS 解析异常: {str(e)}")
                return False

        else:
            print(f"❌ API 请求失败")
            print(f"   状态码: {response.status_code}")
            print(f"   错误: {response.text if hasattr(response, 'text') else 'N/A'}")

    except Exception as e:
        print(f"❌ 请求异常: {str(e)}")
        return False

    # 步骤 3: 显示使用说明
    print("\n" + "=" * 60)
    print("📋 使用说明")
    print("   运行: python3 test_twitter_source.py")
    print("   功能:")
    print("   - 测试 RSSHub 服务健康状态")
    print("   - 测试 Twitter 源 API 访问")
    print("   - 显示获取的 Tweet 数据")
    print("")
    print("💡 提示:")
    print("   如果看到 Tweet 数据，说明 Twitter 源工作正常")
    print("   如果显示错误，请检查 RSSHub 服务")
    print("")

if __name__ == "__main__":
    test_twitter_source()
