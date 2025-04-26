import json
import os
import boto3
import logging
from datetime import datetime
from app.utils.retry import with_sync_retry
from typing import Dict, Any

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# 初始化 DynamoDB 客戶端
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.getenv('DYNAMODB_TABLE_NAME'))

# 初始化 SQS 客戶端
sqs = boto3.client('sqs')
classifier_queue_url = os.getenv('CLASSIFIER_QUEUE_URL')
processor_queue_url = os.getenv('PROCESSOR_QUEUE_URL')

# 獲取環境變數
DYNAMODB_TABLE_NAME = os.environ['DYNAMODB_TABLE_NAME']
CLASSIFIER_QUEUE_URL = os.environ['CLASSIFIER_QUEUE_URL']

@with_sync_retry(max_attempts=3, min_wait=1, max_wait=5)
def save_to_dynamodb(message: Dict[str, Any]) -> None:
    """保存消息到 DynamoDB"""
    try:
        table.put_item(Item=message)
        logger.info(f"Message saved to DynamoDB: {message['messageId']}")
    except Exception as e:
        logger.error(f"Error saving to DynamoDB: {str(e)}")
        raise

@with_sync_retry(max_attempts=3, min_wait=1, max_wait=5)
def send_to_processor_queue(message):
    """發送消息到處理隊列"""
    sqs.send_message(
        QueueUrl=processor_queue_url,
        MessageBody=json.dumps(message)
    )
    logger.info(f"Message sent to processor queue: {message}")

def classify_message(text: str) -> str:
    """分類消息類型"""
    text = text.lower()
    
    if any(word in text for word in ['你好', '嗨', '哈囉', '早安', '午安', '晚安']):
        return 'greeting'
    elif any(word in text for word in ['問題', '請問', '如何', '怎麼', '為什麼']):
        return 'question'
    elif any(word in text for word in ['圖片', '照片', '圖像']):
        return 'image'
    elif any(word in text for word in ['影片', '視頻', '錄影']):
        return 'video'
    elif any(word in text for word in ['語音', '聲音', '錄音']):
        return 'voice'
    else:
        return 'text'

def lambda_handler(event, context):
    try:
        # 從 SQS 事件中獲取消息
        for record in event['Records']:
            message = json.loads(record['body'])
            
            # 分類消息
            classification = classify_message(message['text'])
            message['classification'] = classification
            
            # 保存到 DynamoDB
            save_to_dynamodb(message)
            
            # 發送到分類隊列
            send_to_processor_queue(message)
        
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