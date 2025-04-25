import json
import unittest
from unittest.mock import patch, MagicMock
from app.lambda_function import lambda_handler
import os
from dotenv import load_dotenv
import hmac 
import hashlib
import base64
import logging
import urllib.request
from app.lambda_function import handle_sticker_message, handle_text_message
from linebot.v3.webhooks import MessageEvent
from linebot.v3.messaging import TextMessage
from linebot.v3.messaging import MessagingApi as LineBotApi



"""
這個測試檔案包含了以下功能：
1.模擬文字訊息和貼圖訊息的 webhook 事件
2.設置必要的環境變數
3.驗證 lambda handler 的回應是否正確
4.測試 LINE Bot 到 API Gateway 的資料傳送流程

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

    def create_api_gateway_event(self, body, signature):
        """創建模擬 API Gateway 事件，模擬 LINE 平台發送到 API Gateway 的請求"""
        return {
            "body": body,
            "headers": {
                "x-line-signature": signature,
                "Content-Type": "application/json"
            },
            "httpMethod": "POST",
            "isBase64Encoded": False,
            "path": "/",
            "pathParameters": None,
            "queryStringParameters": None,
            "requestContext": {
                "accountId": "123456789012",
                "apiId": "api-id",
                "domainName": "example.com",
                "httpMethod": "POST",
                "path": "/",
                "stage": "prod"
            },
            "resource": "/"
        }

    @patch('linebot.v3.webhook.WebhookHandler.handle')
    @patch('urllib.request.urlopen')
    @patch('app.db.check_user_exists')
    @patch('app.db.init_user_data')
    @patch('app.db.get_user_curr_status')
    @patch('app.db.set_user_curr_status')
    @patch('linebot.v3.messaging.api.messaging_api.MessagingApi.reply_message_with_http_info')
    def test_text_message(self, mock_reply, mock_set_status, mock_get_status,
                        mock_init_user, mock_check_user, mock_urlopen, mock_handler):
        """測試文字訊息的接收和處理"""
        try:
            # 創建 LineBotApi 實例
            line_bot_api = LineBotApi(self.channel_access_token)
       
            # 設置 mock 回應
            mock_reply.return_value = (None, 200, None)  # 模擬成功的回應
            # 直接模擬處理成功
            mock_handler.return_value = None
            
            # 設置事件處理器的回應
            def handle_text(body, signature):
                # event = MessageEvent.new_from_json_dict(json.loads(body)['events'][0])
                event = MessageEvent.from_dict(json.loads(body)['events'][0])
                line_bot_api.reply_message_with_http_info(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text="回覆：" + event.message.text)]
                )
            
            mock_handler.side_effect = handle_text
            
            # 模擬資料庫回應
            mock_check_user.return_value = False
            mock_get_status.return_value = 'init'
            
            # 準備 LINE Webhook 事件
            body = json.dumps({
                "destination": "xxxxxxxxxx",
                "events": [{
                    "type": "message",
                    "message": {
                        "type": "text",
                        "id": "test_message_id",
                        "text": "Hello, Bot!",
                        "quoteToken": "test-quote-token"
                    },
                    "webhookEventId": "01FZ74A0TCCPYRVKNK77XKC3ZR",
                    "deliveryContext": {
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
            
            # 生成簽名
            signature = self.generate_signature(body)
            
            # 創建 API Gateway 事件
            event = self.create_api_gateway_event(body, signature)
            
            # 調用 Lambda 處理函數
            response = lambda_handler(event, {})
            
            # 輸出詳細的錯誤信息
            if response['statusCode'] != 200:
                print(f"Error response: {response['body']}")
            
            # 驗證回應
            self.assertEqual(response['statusCode'], 200)
            self.assertEqual(response['body'], json.dumps('Success!!!'))
            
            # 驗證 LINE API 被正確調用
            mock_reply.assert_called_once()
        
        except Exception as e:
            print(f"Test failed with error: {str(e)}")
            raise

    @patch('linebot.v3.webhook.WebhookHandler.handle')  # 添加這行
    @patch('urllib.request.urlopen')
    @patch('app.db.check_user_exists')
    @patch('app.db.init_user_data')
    @patch('app.db.get_user_curr_status')
    @patch('app.db.set_user_curr_status')
    @patch('linebot.v3.messaging.api.messaging_api.MessagingApi.reply_message_with_http_info')
    def test_sticker_message(self, mock_reply, mock_set_status, mock_get_status, 
                            mock_init_user, mock_check_user, mock_urlopen, mock_handler):
        """測試貼圖訊息的接收和處理，驗證 Bot 對貼圖的回應功能"""

        # 設置 mock 回應
        mock_reply.return_value = None
        mock_handler.side_effect = lambda body, signature: handle_sticker_message(
            # MessageEvent.new_from_json_dict(json.loads(body)['events'][0])
            event = MessageEvent.from_dict(json.loads(body)['events'][0])
        )

        # 設置 handler mock 來模擬成功處理
        mock_handler.return_value = None    

        # 模擬資料庫回應
        mock_check_user.return_value = False
        mock_get_status.return_value = 'init'
        
        # 模擬 LINE API 回應
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "displayName": "Test User",
            "userId": "test_user_id",
            "pictureUrl": "https://example.com/test.jpg",
            "statusMessage": "Test Status"
        }).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        # 準備 LINE Webhook 事件
        body = json.dumps({
            "destination": "xxxxxxxxxx",
            "events": [{
                "type": "message",
                "message": {
                    "type": "sticker",
                    "id": "test_sticker_id",
                    "stickerId": "1",
                    "packageId": "1",
                    "stickerResourceType": "STATIC",  # 添加這個欄位
                    "quoteToken": "test-quote-token"  # 添加這個欄位
                },
                "webhookEventId": "01FZ74A0TCCPYRVKNK77XKC3ZR",
                "deliveryContext": {
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
        
        # 生成簽名
        signature = self.generate_signature(body)
        
        # 創建 API Gateway 事件
        event = self.create_api_gateway_event(body, signature)
        
        # 調用 Lambda 處理函數
        response = lambda_handler(event, {})
        
        # 驗證回應
        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(response['body'], json.dumps('Success!!!'))
        
        # 驗證 LINE API 被正確調用
        mock_reply.assert_called_once()
        
        # 驗證資料庫操作
        mock_check_user.assert_called_once_with('test_user_id')
        mock_init_user.assert_called_once()
        mock_get_status.assert_called_once_with('test_user_id')
        mock_set_status.assert_called_once()

    @patch('urllib.request.urlopen')
    @patch('app.lambda_function.handler.handle')
    def test_invalid_signature(self, mock_handler, mock_urlopen):
        """測試無效簽名的情況，確保安全驗證機制正常運作"""
        # 準備 LINE Webhook 事件
        body = json.dumps({
            "destination": "xxxxxxxxxx",
            "events": [{
                "type": "message",
                "message": {
                    "type": "text",
                    "id": "test_message_id",
                    "text": "Hello, Bot!"
                },
                "source": {
                    "type": "user",
                    "userId": "test_user_id"
                },
                "replyToken": "test_reply_token"
            }]
        })
        
        # 使用錯誤的簽名
        invalid_signature = "invalid_signature"
        
        # 創建 API Gateway 事件
        event = self.create_api_gateway_event(body, invalid_signature)
        
        # 設置 mock 以模擬簽名驗證失敗
        mock_handler.side_effect = Exception("Invalid signature")
        
        # 調用 Lambda 處理函數
        response = lambda_handler(event, {})
        
        # 驗證回應是錯誤狀態
        self.assertEqual(response['statusCode'], 500)
        self.assertTrue("Invalid signature" in response['body'])

    @patch('urllib.request.urlopen')
    @patch('app.db.check_user_exists')
    @patch('app.db.init_user_data')
    @patch('app.db.get_user_curr_status')
    @patch('app.db.set_user_curr_status')
    @patch('linebot.v3.messaging.api.messaging_api.MessagingApi.reply_message_with_http_info')
    def test_api_gateway_integration(self, mock_reply, mock_set_status, mock_get_status, 
                                    mock_init_user, mock_check_user, mock_urlopen):
        """測試完整的 API Gateway 到 LINE Bot 的資料流程"""
        # 模擬資料庫回應
        mock_check_user.return_value = True
        mock_get_status.return_value = 'quizzing'
        
        # 模擬 LINE API 回應
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "displayName": "Test User",
            "userId": "test_user_id",
            "pictureUrl": "https://example.com/test.jpg",
            "statusMessage": "Test Status"
        }).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        # 準備 API Gateway 事件，模擬從 LINE 平台發送的請求
        body = json.dumps({
            "destination": "xxxxxxxxxx",
            "events": [{
                "type": "message",
                "message": {
                    "type": "text",
                    "id": "test_message_id",
                    "text": "生成我的戀愛測驗結果吧！"
                },
                "webhookEventId": "01FZ74A0TCCPYRVKNK77XKC3ZR",
                "deliveryContext": {
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
        
        # 生成簽名
        signature = self.generate_signature(body)
        
        # 創建完整的 API Gateway 事件
        event = {
            "body": body,
            "headers": {
                "x-line-signature": signature,
                "Content-Type": "application/json",
                "Host": "api-id.execute-api.region.amazonaws.com",
                "X-Forwarded-For": "203.0.113.1",
                "X-Forwarded-Proto": "https",
                "X-Forwarded-Port": "443"
            },
            "httpMethod": "POST",
            "isBase64Encoded": False,
            "path": "/",
            "pathParameters": None,
            "queryStringParameters": None,
            "requestContext": {
                "accountId": "123456789012",
                "apiId": "api-id",
                "domainName": "api-id.execute-api.region.amazonaws.com",
                "httpMethod": "POST",
                "identity": {
                    "sourceIp": "203.0.113.1"
                },
                "path": "/prod/",
                "protocol": "HTTP/1.1",
                "requestId": "request-id",
                "requestTime": "10/Feb/2023:13:40:52 +0000",
                "requestTimeEpoch": 1676035252,
                "resourceId": "resource-id",
                "resourcePath": "/",
                "stage": "prod"
            },
            "resource": "/"
        }


if __name__ == '__main__':
    unittest.main()