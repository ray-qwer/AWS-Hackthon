import json
import os
import boto3
import time
from time import sleep
import logging

from linebot.v3 import WebhookHandler
from linebot.v3.messaging import (
    ApiClient,
    Configuration,
    MessagingApi,
    ReplyMessageRequest,
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent,
    StickerMessageContent,
    FollowEvent
)
import urllib.request

from .app import run

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# 測試時需要
if not os.getenv('AWS_LAMBDA_FUNCTION_NAME'):  # 檢查是否在 Lambda 環境
    from dotenv import load_dotenv
    load_dotenv()

configuration = Configuration(access_token=os.getenv('CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('CHANNEL_SECRET'))


# 使用單一通用處理器
@handler.add(MessageEvent)
def handle_message(event):
    user_id = event.source.user_id
    
    # 統一處理不同消息類型
    if isinstance(event.message, TextMessageContent):
        user_message = event.message.text
    elif isinstance(event.message, StickerMessageContent):
        sticker_id = event.message.sticker_id
        package_id = event.message.package_id
        user_message = f"[STICKER] package_id={package_id}, sticker_id={sticker_id}"
    else:
        user_message = "[不支持的消息類型]"
    
    profile_url = f'https://api.line.me/v2/bot/profile/{user_id}'
    headers = {
        'Authorization': f'Bearer {os.getenv("CHANNEL_ACCESS_TOKEN")}'
    }
    
    req = urllib.request.Request(profile_url, headers=headers)
    
    logger.info(f"發送請求獲取用戶資料: {profile_url}")
    with urllib.request.urlopen(req) as response:
        profile_json = json.loads(response.read().decode('utf-8'))
    
    logger.info(f"獲取到用戶資料: {profile_json}")
    user_name = profile_json.get('displayName', '朋友')
    
    logger.info(f"Received message from {user_id}: {user_message}")
    
    response = run(user_id, user_name, user_message)

    logger.info(f"Response: {response}")
    
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=response
            )
        )

# 專門處理文字訊息的處理器，用於測試
def handle_text_message(event):
    """處理文字訊息的專用函數，委派給通用處理器"""
    logger.info("Handling text message...")
    handle_message(event)
    # 不需要返回值，因為 handle_message 已經處理了回覆

# 專門處理貼圖訊息的處理器，用於測試
def handle_sticker_message(event):
    """處理貼圖訊息的專用函數，委派給通用處理器"""
    logger.info("Handling sticker message...")
    handle_message(event)
    # 不需要返回值，因為 handle_message 已經處理了回覆

def lambda_handler(event, context):
    try: 
        logger.info(f"Received event: {json.dumps(event)}")
        body = event['body']
        signature = event['headers']['x-line-signature']
        logger.info(f"Handling request with signature: {signature}")
        handler.handle(body, signature)
        logger.info("Request handled successfully")
        return {
            'statusCode': 200,
            'body': json.dumps('Success!!!')
        }
    except Exception as e:
        logger.error(f"Error in lambda_handler: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps(str(e))
        }




