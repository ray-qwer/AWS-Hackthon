import json
import os
import boto3
import logging
import hmac
import hashlib
import base64
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage
from app.utils.retry import with_sync_retry

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# 初始化 LINE Bot 處理器
handler = WebhookHandler(os.getenv('CHANNEL_SECRET'))
line_bot_api = LineBotApi(os.getenv('CHANNEL_ACCESS_TOKEN'))

# 初始化 SQS 客戶端
sqs = boto3.client('sqs')
queue_url = os.getenv('SQS_QUEUE_URL')

# 測試時需要
if not os.getenv('AWS_LAMBDA_FUNCTION_NAME'):
    from dotenv import load_dotenv
    load_dotenv()

def verify_signature(body, signature):
    """驗證 LINE 簽名"""
    hash = hmac.new(
        os.getenv('CHANNEL_SECRET').encode('utf-8'),
        body.encode('utf-8'),
        hashlib.sha256
    ).digest()
    return signature == base64.b64encode(hash).decode('utf-8')

def lambda_handler(event, context):
    """Lambda 處理函數"""
    try:
        # 獲取請求頭和體
        headers = event['headers']
        body = event['body']
        
        # 驗證簽名
        signature = headers.get('x-line-signature', '')
        if not verify_signature(body, signature):
            logger.error("Invalid signature")
            return {'statusCode': 400, 'body': 'Invalid signature'}
        
        # 解析事件
        events = json.loads(body)['events']
        
        # 處理每個事件
        for event in events:
            if isinstance(event, MessageEvent):
                # 發送到 SQS
                message = {
                    'messageId': event.message.id,
                    'userId': event.source.user_id,
                    'text': event.message.text,
                    'timestamp': event.timestamp
                }
                
                sqs.send_message(
                    QueueUrl=queue_url,
                    MessageBody=json.dumps(message)
                )
                
                logger.info(f"Message sent to SQS: {message}")
        
        return {'statusCode': 200, 'body': 'OK'}
        
    except InvalidSignatureError:
        logger.error("Invalid signature")
        return {'statusCode': 400, 'body': 'Invalid signature'}
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return {'statusCode': 500, 'body': str(e)}

@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    try:
        # 構建消息對象
        message = {
            'user_id': event.source.user_id,
            'reply_token': event.reply_token,
            'category': 'text',
            'content': event.message.text,
            'timestamp': event.timestamp
        }
        
        # 發送到 SQS
        sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(message)
        )
        
        # 發送確認消息
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text="已收到您的消息，正在處理中...")]
            )
        )
    except Exception as e:
        logger.error(f"Error in handle_text_message: {str(e)}")

@handler.add(MessageEvent, message=ImageMessage)
def handle_image_message(event):
    try:
        # 獲取圖片內容
        message_content = line_bot_api.get_message_content(event.message.id)
        
        # 構建消息對象
        message = {
            'user_id': event.source.user_id,
            'reply_token': event.reply_token,
            'category': 'image',
            'content': message_content.content,
            'timestamp': event.timestamp
        }
        
        # 發送到 SQS
        sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(message)
        )
        
        # 發送確認消息
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text="已收到您的圖片，正在處理中...")]
            )
        )
    except Exception as e:
        logger.error(f"Error in handle_image_message: {str(e)}")

@handler.add(MessageEvent, message=VideoMessage)
def handle_video_message(event):
    try:
        # 獲取影片內容
        message_content = line_bot_api.get_message_content(event.message.id)
        
        # 構建消息對象
        message = {
            'user_id': event.source.user_id,
            'reply_token': event.reply_token,
            'category': 'video',
            'content': message_content.content,
            'timestamp': event.timestamp
        }
        
        # 發送到 SQS
        sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(message)
        )
        
        # 發送確認消息
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text="已收到您的影片，正在處理中...")]
            )
        )
    except Exception as e:
        logger.error(f"Error in handle_video_message: {str(e)}")

@handler.add(MessageEvent, message=AudioMessage)
def handle_audio_message(event):
    try:
        # 獲取音頻內容
        message_content = line_bot_api.get_message_content(event.message.id)
        
        # 構建消息對象
        message = {
            'user_id': event.source.user_id,
            'reply_token': event.reply_token,
            'category': 'voice',
            'content': message_content.content,
            'timestamp': event.timestamp
        }
        
        # 發送到 SQS
        sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(message)
        )
        
        # 發送確認消息
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text="已收到您的語音，正在處理中...")]
            )
        )
    except Exception as e:
        logger.error(f"Error in handle_audio_message: {str(e)}") 