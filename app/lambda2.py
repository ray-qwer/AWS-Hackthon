import json
import os
import boto3
import logging
import requests
from linebot.v3.messaging import MessagingApi
from linebot.v3.messaging import TextMessage, StickerMessage
from musetalk.inference import model_fn, transform_fn
from app.utils.retry import with_sync_retry
from typing import Dict, Any, Optional
from datetime import datetime

# 配置日誌
logger = logging.getLogger()
logger.setLevel(os.getenv('LOG_LEVEL', 'INFO'))
if os.getenv('DEBUG', 'false').lower() == 'true':
    logger.setLevel(logging.DEBUG)

# 初始化 LINE Bot API
try:
    line_bot_api = MessagingApi(os.getenv('CHANNEL_ACCESS_TOKEN'))
except Exception as e:
    logger.error(f"Failed to initialize LINE Bot API: {str(e)}")
    raise

# 初始化 S3 客戶端
try:
    s3 = boto3.client('s3')
    generated_images_bucket = os.getenv('GENERATED_IMAGES_BUCKET_NAME')
    reel_s3_bucket = os.getenv('REEL_S3_BUCKET_NAME')
except Exception as e:
    logger.error(f"Failed to initialize S3 client: {str(e)}")
    raise

# 初始化 Bedrock 客戶端
bedrock = boto3.client('bedrock-runtime')
model_id = "amazon.nova-pro-v1:0"

# 初始化 MuseTalk 模型
model = model_fn('/opt/ml/model')

# 遊戲橘子 API 配置
PUBLIC_VOICE_API_URL = "https://api.gamania.com/public-voice"
PUBLIC_VOICE_API_KEY = os.getenv('PUBLIC_VOICE_API_KEY')

@with_sync_retry(max_attempts=3, min_wait=1, max_wait=5)
def generate_content_with_nova(prompt: str) -> str:
    """使用 Nova 生成內容"""
    try:
        response = requests.post(
            'https://api.nova.ai/v1/generate',
            headers={'Authorization': f'Bearer {os.getenv("NOVA_API_KEY")}'},
            json={'prompt': prompt}
        )
        response.raise_for_status()
        return response.json()['content']
    except Exception as e:
        logger.error(f"Failed to generate content with Nova: {str(e)}")
        raise

@with_sync_retry(max_attempts=3, min_wait=1, max_wait=5)
def synthesize_voice(text: str) -> str:
    """合成語音"""
    try:
        response = requests.post(
            'https://api.publicvoice.ai/v1/synthesize',
            headers={'Authorization': f'Bearer {os.getenv("PUBLIC_VOICE_API_KEY")}'},
            json={'text': text}
        )
        response.raise_for_status()
        return response.json()['audio_url']
    except Exception as e:
        logger.error(f"Failed to synthesize voice: {str(e)}")
        raise

@with_sync_retry(max_attempts=3, min_wait=1, max_wait=5)
def upload_to_s3(bucket: str, key: str, content: bytes) -> str:
    """上傳內容到 S3"""
    try:
        s3.put_object(
            Bucket=bucket,
            Key=key,
            Body=content
        )
        return f"https://{bucket}.s3.amazonaws.com/{key}"
    except Exception as e:
        logger.error(f"Failed to upload to S3: {str(e)}")
        raise

@with_sync_retry(max_attempts=3, min_wait=1, max_wait=5)
def send_reply_message(reply_token: str, messages: list) -> None:
    """發送回復消息"""
    try:
        line_bot_api.reply_message(
            reply_token=reply_token,
            messages=messages
        )
    except Exception as e:
        logger.error(f"Failed to send reply message: {str(e)}")
        raise

def generate_text(prompt: str) -> str:
    """生成文本"""
    try:
        logger.info(f"Generating text for prompt: {prompt}")
        return generate_content_with_nova(prompt)
    except Exception as e:
        logger.error(f"Failed to generate text: {str(e)}")
        return "抱歉，我現在無法生成文本。"

def generate_voice(text: str) -> str:
    """生成語音"""
    try:
        logger.info(f"Generating voice for text: {text}")
        return synthesize_voice(text)
    except Exception as e:
        logger.error(f"Failed to generate voice: {str(e)}")
        return "抱歉，我現在無法生成語音。"

def process_video(audio_url: str) -> str:
    """處理視頻"""
    try:
        logger.info(f"Processing video with audio: {audio_url}")
        # 下載音頻
        audio_response = requests.get(audio_url)
        audio_response.raise_for_status()
        
        # 使用 MuseTalk 處理視頻
        video_content = model_fn(audio_response.content)
        
        # 上傳到 S3
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        video_key = f'videos/{timestamp}.mp4'
        return upload_to_s3(reel_s3_bucket, video_key, video_content)
    except Exception as e:
        logger.error(f"Failed to process video: {str(e)}")
        return "抱歉，我現在無法處理視頻。"

def save_to_s3(content: bytes, bucket: str, key: str) -> str:
    """保存內容到 S3"""
    try:
        logger.info(f"Saving content to S3: {bucket}/{key}")
        return upload_to_s3(bucket, key, content)
    except Exception as e:
        logger.error(f"Failed to save to S3: {str(e)}")
        raise

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Lambda 處理函數"""
    try:
        for record in event['Records']:
            try:
                message = json.loads(record['body'])
                logger.info(f"Processing message: {message}")

                if message['type'] == 'text':
                    handle_text_message(message)
                elif message['type'] == 'audio':
                    handle_voice_message(message)
                elif message['type'] == 'video':
                    handle_video_message(message)
                else:
                    handle_unsupported_message(message)

            except Exception as e:
                logger.error(f"Failed to process message: {str(e)}")
                continue

        return {'statusCode': 200, 'body': 'OK'}
    except Exception as e:
        logger.error(f"Lambda handler error: {str(e)}")
        return {'statusCode': 500, 'body': 'Internal Server Error'}

def handle_text_message(message: Dict[str, Any]) -> None:
    """處理文本消息"""
    try:
        logger.info(f"Handling text message: {message}")
        text = generate_text(message['message'])
        send_reply_message(
            message['reply_token'],
            [TextMessage(text=text)]
        )
    except Exception as e:
        logger.error(f"Failed to handle text message: {str(e)}")
        raise

def handle_voice_message(message: Dict[str, Any]) -> None:
    """處理語音消息"""
    try:
        logger.info(f"Handling voice message: {message}")
        audio_url = generate_voice(message['message'])
        send_reply_message(
            message['reply_token'],
            [TextMessage(text=f"語音已生成: {audio_url}")]
        )
    except Exception as e:
        logger.error(f"Failed to handle voice message: {str(e)}")
        raise

def handle_video_message(message: Dict[str, Any]) -> None:
    """處理視頻消息"""
    try:
        logger.info(f"Handling video message: {message}")
        video_url = process_video(message['message'])
        send_reply_message(
            message['reply_token'],
            [TextMessage(text=f"視頻已處理: {video_url}")]
        )
    except Exception as e:
        logger.error(f"Failed to handle video message: {str(e)}")
        raise

def handle_unsupported_message(message: Dict[str, Any]) -> None:
    """處理不支持的消息類型"""
    try:
        logger.warning(f"Unsupported message type: {message['type']}")
        send_reply_message(
            message['reply_token'],
            [TextMessage(text="抱歉，我不支持這種類型的消息。")]
        )
    except Exception as e:
        logger.error(f"Failed to handle unsupported message: {str(e)}")
        raise 