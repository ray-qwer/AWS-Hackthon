import json
import os
import boto3
import logging
from datetime import datetime
from app.utils.retry import with_sync_retry
from typing import Dict, Any, Optional

# 配置日誌
logger = logging.getLogger()
logger.setLevel(os.getenv('LOG_LEVEL', 'INFO'))
if os.getenv('DEBUG', 'false').lower() == 'true':
    logger.setLevel(logging.DEBUG)

# 初始化 DynamoDB 客戶端
try:
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(os.getenv('DYNAMODB_TABLE_NAME'))
except Exception as e:
    logger.error(f"Failed to initialize DynamoDB: {str(e)}")
    raise

# 初始化 SQS 客戶端
try:
    sqs = boto3.client('sqs')
    classifier_queue_url = os.getenv('CLASSIFIER_QUEUE_URL')
    processor_queue_url = os.getenv('PROCESSOR_QUEUE_URL')
except Exception as e:
    logger.error(f"Failed to initialize SQS: {str(e)}")
    raise

# 獲取環境變數
DYNAMODB_TABLE_NAME = os.environ['DYNAMODB_TABLE_NAME']
CLASSIFIER_QUEUE_URL = os.environ['CLASSIFIER_QUEUE_URL']

@with_sync_retry(max_attempts=3, min_wait=1, max_wait=5)
def save_to_dynamodb(message: Dict[str, Any]) -> None:
    """保存消息到 DynamoDB"""
    try:
        item = {
            'user_id': message['user_id'],
            'timestamp': str(datetime.now().timestamp()),
            'message_type': message['type'],
            'content': message.get('message', ''),
            'status': 'classified'
        }
        response = table.put_item(Item=item)
        logger.debug(f"Message saved to DynamoDB: {response}")
    except Exception as e:
        logger.error(f"Failed to save message to DynamoDB: {str(e)}")
        raise

@with_sync_retry(max_attempts=3, min_wait=1, max_wait=5)
def send_to_processor_queue(message: Dict[str, Any]) -> None:
    """發送消息到處理隊列"""
    try:
        response = sqs.send_message(
            QueueUrl=processor_queue_url,
            MessageBody=json.dumps(message)
        )
        logger.debug(f"Message sent to processor queue: {response['MessageId']}")
    except Exception as e:
        logger.error(f"Failed to send message to processor queue: {str(e)}")
        raise

def classify_message(text: str) -> str:
    """分類消息類型"""
    try:
        # 簡單的關鍵詞分類
        text = text.lower()
        if any(word in text for word in ['hi', 'hello', '你好', '嗨']):
            return 'greeting'
        elif any(word in text for word in ['help', '幫助', '怎麼用']):
            return 'help'
        elif any(word in text for word in ['bye', '再見', '拜拜']):
            return 'farewell'
        else:
            return 'general'
    except Exception as e:
        logger.error(f"Failed to classify message: {str(e)}")
        return 'general'

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Lambda 處理函數"""
    try:
        for record in event['Records']:
            try:
                # 解析 SQS 消息
                message = json.loads(record['body'])
                logger.info(f"Processing message: {message}")

                # 保存到 DynamoDB
                save_to_dynamodb(message)

                # 分類消息
                if message['type'] == 'text':
                    message['category'] = classify_message(message['message'])
                else:
                    message['category'] = message['type']

                # 發送到處理隊列
                send_to_processor_queue(message)

            except Exception as e:
                logger.error(f"Failed to process message: {str(e)}")
                continue

        return {'statusCode': 200, 'body': 'OK'}
    except Exception as e:
        logger.error(f"Lambda handler error: {str(e)}")
        return {'statusCode': 500, 'body': 'Internal Server Error'} 