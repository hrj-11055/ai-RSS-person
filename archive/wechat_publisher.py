import requests
import json
from wechatpy import WeChatClient

# ================= 配置区域 =================
# 在微信公众号后台 -> 开发 -> 基本配置里找
APP_ID = "wxfe38b8be5c15aba5"
APP_SECRET = "b1596b85154d2fde3c45ed2eccbc1e53"

# 准备一张封面图，放在脚本同级目录下，比如叫 cover.jpg
COVER_IMAGE_PATH = "cover.png" 

class WeChatAuto:
    def __init__(self):
        try:
            self.client = WeChatClient(APP_ID, APP_SECRET)
            print("✅ 微信 AccessToken 获取成功")
        except Exception as e:
            print(f"❌ 微信登录失败 (检查IP白名单?): {e}")
            self.client = None

    def upload_cover(self, image_path):
        """上传封面图，获取 media_id"""
        print("📤 正在上传封面图...")
        try:
            with open(image_path, 'rb') as f:
                # 永久素材上传 (image)
                res = self.client.material.add('image', f)
                media_id = res['media_id']
                print(f"✅ 封面上传成功: {media_id}")
                return media_id
        except Exception as e:
            print(f"❌ 封面上传失败: {e}")
            return None

    def upload_draft(self, title, author, html_content, digest, media_id):
        """上传文章到草稿箱"""
        print("📝 正在创建草稿...")
        
        # 微信文章结构
        article = {
            "title": title,
            "author": author,
            "digest": digest, # 摘要
            "content": html_content, # 正文 (HTML)
            "content_source_url": "", 
            "thumb_media_id": media_id, # 封面ID
            "need_open_comment": 1,
            "only_fans_can_comment": 0
        }

        try:
            # 调用草稿箱 API (add_draft)
            # 注意：wechatpy 的 draft 接口封装可能因版本不同有差异，
            # 这里我们直接用 client 的通用方法调用官方 API，更稳妥。
            
            url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={self.client.access_token}"
            data = {
                "articles": [article]
            }
            # 必须指定 ensure_ascii=False，否则中文会乱码
            response = requests.post(url, data=json.dumps(data, ensure_ascii=False).encode('utf-8'))
            result = response.json()
            
            if "media_id" in result:
                print(f"🎉 草稿创建成功！Media ID: {result['media_id']}")
                return True
            else:
                print(f"❌ 草稿创建失败: {result}")
                return False
                
        except Exception as e:
            print(f"❌ 接口调用出错: {e}")
            return False

if __name__ == "__main__":
    # 测试代码
    bot = WeChatAuto()
    if bot.client:
        mid = bot.upload_cover(COVER_IMAGE_PATH)
        if mid:
            bot.upload_draft(
                title="Python自动发布测试",
                author="AI助手",
                html_content="<h1>你好</h1><p>这是正文</p>",
                digest="这是摘要",
                media_id=mid
            )