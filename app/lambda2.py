import json
import os
import boto3
import logging
import requests
from linebot.v3.messaging import MessagingApi
from linebot.v3.messaging import TextMessage, StickerMessage
from musetalk.inference import model_fn, transform_fn
from app.utils.retry import with_sync_retry
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# 初始化 LINE Bot API
line_bot_api = MessagingApi(os.getenv('CHANNEL_ACCESS_TOKEN'))

# 初始化 S3 客戶端
s3 = boto3.client('s3')
output_bucket = os.getenv('GENERATED_IMAGES_BUCKET_NAME')
reel_bucket = os.getenv('REEL_S3_BUCKET_NAME')

# 初始化 Bedrock 客戶端
bedrock = boto3.client('bedrock-runtime')
model_id = "amazon.nova-pro-v1:0"

# 初始化 MuseTalk 模型
model = model_fn('/opt/ml/model')

# 遊戲橘子 API 配置
PUBLIC_VOICE_API_URL = "https://api.gamania.com/public-voice"
PUBLIC_VOICE_API_KEY = os.getenv('PUBLIC_VOICE_API_KEY')

@with_sync_retry(max_attempts=3, min_wait=1, max_wait=5)
def generate_content_with_nova(prompt):
    """使用 Bedrock Nova 生成內容"""
    response = bedrock.invoke_model(
        modelId=model_id,
        body=json.dumps({
            "prompt": prompt,
            "max_tokens": 1000,
            "temperature": 0.7
        })
    )
    
    result = json.loads(response['body'].read())
    return result['completion'].strip()

@with_sync_retry(max_attempts=3, min_wait=1, max_wait=5)
def synthesize_voice(text):
    """使用遊戲橘子 API 合成語音"""
    headers = {
        'Authorization': f'Bearer {PUBLIC_VOICE_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    data = {
        'text': text,
        'mode': 'stream'
    }
    
    response = requests.post(
        PUBLIC_VOICE_API_URL,
        headers=headers,
        json=data
    )
    
    if response.status_code == 200:
        result = response.json()
        return result.get('media_url')
    else:
        logger.error(f"Error in synthesize_voice: {response.text}")
        return None

@with_sync_retry(max_attempts=3, min_wait=1, max_wait=5)
def upload_to_s3(bucket, key, content):
    """上傳內容到 S3"""
    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=content
    )

@with_sync_retry(max_attempts=3, min_wait=1, max_wait=5)
def send_reply_message(reply_token, messages):
    """發送回覆消息"""
    line_bot_api.reply_message_with_http_info(
        reply_token,
        messages
    )

def generate_text(prompt: str) -> str:
    """使用 Bedrock Nova 生成文本"""
    try:
        response = bedrock.invoke_model(
            modelId='anthropic.claude-v2',
            body=json.dumps({
                'prompt': prompt,
                'max_tokens_to_sample': 1000,
                'temperature': 0.7
            })
        )
        return json.loads(response['body'].read())['completion']
    except Exception as e:
        logger.error(f"Error generating text: {str(e)}")
        raise

def generate_voice(text: str) -> str:
    """使用遊戲橘子 API 生成語音"""
    try:
        response = requests.post(
            'https://api.gamania.com/voice',
            headers={'Authorization': f'Bearer {PUBLIC_VOICE_API_KEY}'},
            json={'text': text, 'mode': 'stream'}
        )
        response.raise_for_status()
        return response.json()['media_url']
    except Exception as e:
        logger.error(f"Error generating voice: {str(e)}")
        raise

def process_video(audio_url: str) -> str:
    """使用 MuseTalk 處理視頻"""
    try:
        # 下載音頻
        audio_response = requests.get(audio_url)
        audio_response.raise_for_status()
        
        # 上傳到 S3
        timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        audio_key = f'temp/audio_{timestamp}.wav'
        s3.put_object(
            Bucket=reel_bucket,
            Key=audio_key,
            Body=audio_response.content
        )
        
        # 調用 MuseTalk API
        musetalk_response = requests.post(
            'https://api.musetalk.com/process',
            json={'audio_key': audio_key}
        )
        musetalk_response.raise_for_status()
        
        return musetalk_response.json()['video_url']
        
    except Exception as e:
        logger.error(f"Error processing video: {str(e)}")
        raise

def save_to_s3(content: bytes, bucket: str, key: str) -> str:
    """保存內容到 S3"""
    try:
        s3.put_object(
            Bucket=bucket,
            Key=key,
            Body=content
        )
        return f"https://{bucket}.s3.amazonaws.com/{key}"
    except Exception as e:
        logger.error(f"Error saving to S3: {str(e)}")
        raise

def lambda_handler(event, context):
    """Lambda 處理函數"""
    try:
        # 處理 SQS 消息
        for record in event['Records']:
            message = json.loads(record['body'])
            
            # 根據分類處理消息
            if message['classification'] == 'greeting':
                # 生成問候回應
                response_text = generate_text(f"生成一個友好的問候回應：{message['text']}")
                voice_url = generate_voice(response_text)
                
                # 保存到 S3
                timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
                key = f"responses/{message['userId']}/{timestamp}.mp3"
                save_to_s3(requests.get(voice_url).content, output_bucket, key)
                
            elif message['classification'] == 'question':
                # 生成問題回答
                response_text = generate_text(f"回答這個問題：{message['text']}")
                voice_url = generate_voice(response_text)
                video_url = process_video(voice_url)
                
                # 保存到 S3
                timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
                key = f"responses/{message['userId']}/{timestamp}.mp4"
                save_to_s3(requests.get(video_url).content, reel_bucket, key)
                
            # 其他分類的處理...
            
        return {
            'statusCode': 200,
            'body': json.dumps('Messages processed successfully')
        }
        
    except Exception as e:
        logger.error(f"Error in lambda_handler: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(str(e))
        }

def handle_text_message(message):
    """處理文字消息"""
    try:
        # 使用 Nova 生成回應內容
        prompt = f"""
        請根據以下對話生成一個有趣且自然的回應：
        用戶：{message['content']}
        
        請以 Chiikawa 的風格回應。
        """
        
        generated_content = generate_content_with_nova(prompt)
        
        if generated_content:
            # 使用遊戲橘子 API 合成語音
            voice_url = synthesize_voice(generated_content)
            
            if voice_url:
                # 下載語音文件
                voice_response = requests.get(voice_url)
                if voice_response.status_code == 200:
                    # 上傳到 S3
                    s3_key = f"{message['user_id']}/voice.wav"
                    upload_to_s3(output_bucket, s3_key, voice_response.content)
                    
                    # 生成公開訪問 URL
                    voice_s3_url = f"https://{output_bucket}.s3.amazonaws.com/{s3_key}"
                    
                    # 回覆文字和語音
                    send_reply_message(
                        message['reply_token'],
                        [
                            TextMessage(text=generated_content),
                            TextMessage(text=f"語音回應：{voice_s3_url}")
                        ]
                    )
                else:
                    # 如果語音合成失敗，只回覆文字
                    send_reply_message(
                        message['reply_token'],
                        [TextMessage(text=generated_content)]
                    )
            else:
                # 如果語音合成失敗，只回覆文字
                send_reply_message(
                    message['reply_token'],
                    [TextMessage(text=generated_content)]
                )
        else:
            # 如果內容生成失敗，回覆預設消息
            send_reply_message(
                message['reply_token'],
                [TextMessage(text="抱歉，我現在無法回應，請稍後再試。")]
            )
    except Exception as e:
        logger.error(f"Error in handle_text_message: {str(e)}")

def handle_voice_message(message):
    """處理語音消息"""
    try:
        # 使用 MuseTalk 處理語音
        response = transform_fn(
            model,
            {
                'id': message['user_id'],
                'wav': message['content'],
                'vid_name': 'output'
            },
            'application/json',
            'application/json'
        )
        
        # 上傳處理結果到 S3
        output_path = response[0]
        s3_key = f"{message['user_id']}/output.mp4"
        
        with open(output_path, 'rb') as file:
            s3.upload_fileobj(file, output_bucket, s3_key)
        
        # 生成公開訪問 URL
        url = f"https://{output_bucket}.s3.amazonaws.com/{s3_key}"
        
        # 回覆處理結果
        line_bot_api.reply_message_with_http_info(
            message['reply_token'],
            TextMessage(text=f"您的語音已處理完成，請查看：{url}")
        )
    except Exception as e:
        logger.error(f"Error in handle_voice_message: {str(e)}")

def handle_video_message(message):
    """處理影片消息"""
    try:
        # 1. 從 ReelS3 獲取影片素材
        reel_video_key = f"reels/{message['user_id']}/input.mp4"
        reel_video_url = f"https://{reel_bucket}.s3.amazonaws.com/{reel_video_key}"
        
        # 2. 使用 MuseTalk 處理影片
        response = transform_fn(
            model,
            {
                'id': message['user_id'],
                'wav': message['content'],
                'vid_name': 'output',
                'reel_video_url': reel_video_url
            },
            'application/json',
            'application/json'
        )
        
        # 3. 上傳處理結果到 ReelS3
        output_path = response[0]
        output_key = f"reels/{message['user_id']}/output.mp4"
        
        with open(output_path, 'rb') as file:
            upload_to_s3(reel_bucket, output_key, file)
        
        # 4. 生成公開訪問 URL
        output_url = f"https://{reel_bucket}.s3.amazonaws.com/{output_key}"
        
        # 5. 回覆處理結果
        send_reply_message(
            message['reply_token'],
            [TextMessage(text=f"您的影片已處理完成，請查看：{output_url}")]
        )
    except Exception as e:
        logger.error(f"Error in handle_video_message: {str(e)}")

def handle_unsupported_message(message):
    """處理不支援的消息類型"""
    try:
        send_reply_message(
            message['reply_token'],
            [TextMessage(text="抱歉，目前不支援此類型的消息。")]
        )
    except Exception as e:
        logger.error(f"Error in handle_unsupported_message: {str(e)}") 