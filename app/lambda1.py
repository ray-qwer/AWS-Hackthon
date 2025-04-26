import json
import os
import boto3
import logging
from linebot.v3 import WebhookHandler
from linebot.v3.webhooks import MessageEvent, TextMessageContent, StickerMessageContent
import urllib.request

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# 初始化 SQS 客戶端
sqs = boto3.client('sqs')
queue_url = os.getenv('SQS_QUEUE_URL')

# 初始化 Bedrock 客戶端
bedrock = boto3.client('bedrock-runtime')
model_id = "amazon.nova-pro-v1:0"

# 測試時需要
if not os.getenv('AWS_LAMBDA_FUNCTION_NAME'):
    from dotenv import load_dotenv
    load_dotenv()

handler = WebhookHandler(os.getenv('CHANNEL_SECRET'))

def lambda_handler(event, context):
    try:
        logger.info(f"Received event: {json.dumps(event)}")
        body = event['body']
        signature = event['headers']['x-line-signature']
        
        # 驗證 LINE 簽名
        handler.handle(body, signature)
        
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

@handler.add(MessageEvent)
def handle_message(event):
    try:
        # 1. 獲取使用者資訊
        user_id = event.source.user_id
        user_name = get_user_name(user_id)
        
        # 2. 判斷訊息類型
        message_type, content = classify_message(event.message)
        
        # 3. 使用 Bedrock Nova 進行訊息分類
        message_category = classify_with_bedrock(content)
        
        # 4. 構建訊息
        message = {
            'user_id': user_id,
            'user_name': user_name,
            'message_type': message_type,
            'content': content,
            'category': message_category,
            'reply_token': event.reply_token
        }
        
        # 5. 發送到 SQS
        sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(message)
        )
        
        logger.info(f"Message sent to SQS: {message}")
        
    except Exception as e:
        logger.error(f"Error in handle_message: {str(e)}", exc_info=True)

def get_user_name(user_id):
    """獲取 LINE 使用者名稱"""
    try:
        profile_url = f'https://api.line.me/v2/bot/profile/{user_id}'
        headers = {
            'Authorization': f'Bearer {os.getenv("CHANNEL_ACCESS_TOKEN")}'
        }
        
        req = urllib.request.Request(profile_url, headers=headers)
        with urllib.request.urlopen(req) as response:
            profile_json = json.loads(response.read().decode('utf-8'))
            return profile_json.get('displayName', '朋友')
    except Exception as e:
        logger.error(f"Error getting user name: {str(e)}")
        return '朋友'

def classify_message(message):
    """判斷訊息類型"""
    if isinstance(message, TextMessageContent):
        return 'text', message.text
    elif isinstance(message, StickerMessageContent):
        return 'sticker', {
            'package_id': message.package_id,
            'sticker_id': message.sticker_id
        }
    else:
        return 'unsupported', None

def classify_with_bedrock(content):
    """使用 Bedrock Nova 進行訊息分類"""
    try:
        prompt = f"""
        請判斷以下訊息的類型：
        1. 文字對話
        2. 語音對話
        3. 影片對話
        
        訊息內容：{content}
        
        請只回傳數字（1、2 或 3）。
        """
        
        response = bedrock.invoke_model(
            modelId=model_id,
            body=json.dumps({
                "prompt": prompt,
                "max_tokens": 10,
                "temperature": 0
            })
        )
        
        result = json.loads(response['body'].read())
        category = result['completion'].strip()
        
        # 將分類結果轉換為對應的類型
        category_map = {
            '1': 'text',
            '2': 'voice',
            '3': 'video'
        }
        
        return category_map.get(category, 'text')
        
    except Exception as e:
        logger.error(f"Error in classify_with_bedrock: {str(e)}")
        return 'text'  # 預設返回文字類型 