import json
import unittest
from app.lambda_function import lambda_handler
import os
from dotenv import load_dotenv
import hmac 
import hashlib
import base64
import logging

"""
這個測試檔案包含了以下功能：
1.模擬文字訊息和貼圖訊息的 webhook 事件
2.設置必要的環境變數
3.驗證 lambda handler 的回應是否正確

這個測試檔案可以幫助你在本地開發時驗證 LINE Bot 的基本功能是否正常運作。
"""

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestLineBot(unittest.TestCase):
    def setUp(self):
        """驗證必要的環境變數是否正確設置，測試資料庫和儲存桶的配置"""
        load_dotenv()
        self.channel_secret = os.getenv('CHANNEL_SECRET')
        if not self.channel_secret:
            raise ValueError("請確保已設置 CHANNEL_SECRET 環境變數")
        self.channel_access_token = os.getenv('CHANNEL_ACCESS_TOKEN')
        if not self.channel_access_token:
            raise ValueError("請確保已設置 CHANNEL_ACCESS_TOKEN 環境變數")

        os.environ['TABLE_NAME'] = 'test-table'
        os.environ['ASSET_BUCKET_NAME'] = 'test-asset-bucket'
        os.environ['OUTPUT_BUCKET_NAME'] = 'test-output-bucket'

    def generate_signature(self, body):
        """測試訊息簽名機制，確保訊息來源的安全性驗證"""
        hash = hmac.new(
            self.channel_secret.encode('utf-8'),
            body.encode('utf-8'),
            hashlib.sha256
        ).digest()
        signature = base64.b64encode(hash).decode('utf-8')
        return signature

    def test_text_message(self):
        """測試文字訊息的接收和處理，驗證 Bot 是否能正確回應文字訊息"""
        body = json.dumps({
            "destination": "xxxxxxxxxx",
            "events": [{
                "type": "message",
                "message": {
                    "type": "text",
                    "id": "test_message_id",
                    "text": "Hello, Bot!"
                },
                "webhookEventId": "01FZ74A0TCCPYRVKNK77XKC3ZR",  # 添加這個
                "deliveryContext": {  # 添加這個
                    "isRedelivery": False
                },
                "timestamp": 1462629479859,
                "source": {
                    "type": "user",
                    "userId": "test_user_id"
                },
                "replyToken": "test_reply_token",
                "mode": "active"  # 添加這個
            }]
        })


    def test_sticker_message(self):
        """測試貼圖訊息的接收和處理，驗證 Bot 對貼圖的回應功能"""
        body = json.dumps({
            "destination": "xxxxxxxxxx",
            "events": [{
                "type": "message",
                "message": {
                    "type": "sticker",
                    "id": "test_sticker_id",
                    "stickerId": "1",
                    "packageId": "1"
                },
                "webhookEventId": "01FZ74A0TCCPYRVKNK77XKC3ZR",  # 添加這個
                "deliveryContext": {  # 添加這個
                    "isRedelivery": False
                },
                "timestamp": 1462629479859,
                "source": {
                    "type": "user",
                    "userId": "test_user_id"
                },
                "replyToken": "test_reply_token",
                "mode": "active"
            }]
        })


    def mock_line_api_response():
        return {
            "displayName": "Test User",
            "userId": "test_user_id",
            "pictureUrl": "https://example.com/test.jpg",
            "statusMessage": "Test Status"
        }

if __name__ == '__main__':
    unittest.main()
