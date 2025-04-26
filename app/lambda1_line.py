import json
import os
import boto3
import logging
import hmac
import hashlib
import base64
from linebot.v3 import WebhookHandler
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent,
    ImageMessageContent,
    VideoMessageContent,
    AudioMessageContent
)
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage
)
from linebot.v3.exceptions import InvalidSignatureError
from app.utils.retry import with_sync_retry
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# 配置日誌
logger = logging.getLogger()
logger.setLevel(os.getenv('LOG_LEVEL', 'INFO'))
if os.getenv('DEBUG', 'false').lower() == 'true':
    logger.setLevel(logging.DEBUG)

# 載入環境變數
load_dotenv()

# 初始化 LINE Bot
try:
    configuration = Configuration(access_token=os.getenv('CHANNEL_ACCESS_TOKEN'))
    handler = WebhookHandler(os.getenv('CHANNEL_SECRET'))
except Exception as e:
    logger.error(f"Failed to initialize LINE Bot: {str(e)}")
    raise

# 初始化 SQS 客戶端
sqs = boto3.client('sqs')
classifier_queue_url = os.getenv('CLASSIFIER_QUEUE_URL')
processor_queue_url = os.getenv('PROCESSOR_QUEUE_URL')

def verify_signature(body: str, signature: str) -> bool:
    """驗證 LINE 請求的簽名"""
    try:
        channel_secret = os.getenv('CHANNEL_SECRET')
        hash_obj = hmac.new(
            channel_secret.encode('utf-8'),
            body.encode('utf-8'),
            hashlib.sha256
        )
        calculated_signature = base64.b64encode(hash_obj.digest()).decode('utf-8')
        return hmac.compare_digest(calculated_signature, signature)
    except Exception as e:
        logger.error(f"Signature verification failed: {str(e)}")
        return False

@with_sync_retry(max_attempts=3, min_wait=1, max_wait=5)
def send_to_classifier_queue(message: Dict[str, Any]) -> None:
    """發送消息到分類隊列"""
    try:
        response = sqs.send_message(
            QueueUrl=classifier_queue_url,
            MessageBody=json.dumps(message)
        )
        logger.debug(f"Message sent to classifier queue: {response['MessageId']}")
    except Exception as e:
        logger.error(f"Failed to send message to classifier queue: {str(e)}")
        raise

def lambda_handler(event, context):
    """Lambda 處理函數"""
    try:
        # 從 API Gateway 事件中獲取簽名
        signature = event['headers'].get('x-line-signature')
        if not signature:
            logger.error("No signature found in request headers")
            return {'statusCode': 400, 'body': 'No signature'}

        # 獲取請求內容
        body = event['body']
        logger.info(f"Request body: {body}")

        # 驗證簽名
        try:
            handler.handle(body, signature)
        except InvalidSignatureError:
            logger.error("Invalid signature")
            return {'statusCode': 400, 'body': 'Invalid signature'}

        return {'statusCode': 200, 'body': 'OK'}
    except Exception as e:
        logger.error(f"Lambda handler error: {str(e)}")
        return {'statusCode': 500, 'body': str(e)}

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    """處理文字消息"""
    try:
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            # 回覆相同的訊息
            line_bot_api.reply_message_with_http_info(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=event.message.text)]
                )
            )
        logger.info(f"Message sent: {event.message.text}")
    except Exception as e:
        logger.error(f"Error handling message: {str(e)}")
        raise

@handler.add(MessageEvent, message=ImageMessageContent)
def handle_image_message(event: MessageEvent) -> None:
    """處理圖片消息"""
    try:
        logger.info("Received image message")
        message = {
            'type': 'image',
            'user_id': event.source.user_id,
            'message_id': event.message.id,
            'timestamp': event.timestamp
        }
        send_to_classifier_queue(message)
    except Exception as e:
        logger.error(f"Failed to handle image message: {str(e)}")
        raise

@handler.add(MessageEvent, message=VideoMessageContent)
def handle_video_message(event: MessageEvent) -> None:
    """處理視頻消息"""
    try:
        logger.info("Received video message")
        message = {
            'type': 'video',
            'user_id': event.source.user_id,
            'message_id': event.message.id,
            'timestamp': event.timestamp
        }
        send_to_classifier_queue(message)
    except Exception as e:
        logger.error(f"Failed to handle video message: {str(e)}")
        raise

@handler.add(MessageEvent, message=AudioMessageContent)
def handle_audio_message(event: MessageEvent) -> None:
    """處理音頻消息"""
    try:
        logger.info("Received audio message")
        message = {
            'type': 'audio',
            'user_id': event.source.user_id,
            'message_id': event.message.id,
            'timestamp': event.timestamp
        }
        send_to_classifier_queue(message)
    except Exception as e:
        logger.error(f"Failed to handle audio message: {str(e)}")
        raise 