import json
import os
import pytest
from moto import mock_sqs, mock_dynamodb
import boto3
import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lambda1_classifier import lambda_handler, save_to_dynamodb, send_to_processor_queue, classify_message

@pytest.fixture
def sqs_client():
    with mock_sqs():
        client = boto3.client('sqs', region_name='ap-northeast-1')
        queue_url = client.create_queue(QueueName='ProcessorQueue')['QueueUrl']
        os.environ['PROCESSOR_QUEUE_URL'] = queue_url
        yield client

@pytest.fixture
def dynamodb_table():
    with mock_dynamodb():
        client = boto3.resource('dynamodb', region_name='ap-northeast-1')
        table = client.create_table(
            TableName='MessagesTable',
            KeySchema=[
                {'AttributeName': 'user_id', 'KeyType': 'HASH'},
                {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'user_id', 'AttributeType': 'S'},
                {'AttributeName': 'timestamp', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        os.environ['DYNAMODB_TABLE_NAME'] = 'MessagesTable'
        yield table

@pytest.fixture
def sqs_event():
    return {
        'Records': [{
            'body': json.dumps({
                'type': 'text',
                'user_id': 'test_user',
                'message': 'Hello, World!'
            })
        }]
    }

def test_classify_message():
    # 測試消息分類功能
    assert classify_message('Hello') == 'greeting'
    assert classify_message('How to use?') == 'help'
    assert classify_message('Goodbye') == 'farewell'
    assert classify_message('Random message') == 'general'

def test_save_to_dynamodb(dynamodb_table):
    # 測試保存消息到 DynamoDB
    test_message = {
        'user_id': 'test_user',
        'type': 'text',
        'message': 'Hello, World!'
    }
    
    save_to_dynamodb(test_message)
    
    # 驗證消息是否被保存
    response = dynamodb_table.scan()
    assert len(response['Items']) == 1
    saved_item = response['Items'][0]
    assert saved_item['user_id'] == test_message['user_id']
    assert saved_item['message_type'] == test_message['type']

def test_send_to_processor_queue(sqs_client):
    # 測試發送消息到處理隊列
    test_message = {
        'type': 'text',
        'user_id': 'test_user',
        'message': 'Hello, World!'
    }
    
    send_to_processor_queue(test_message)
    
    # 驗證消息是否被發送到隊列
    response = sqs_client.receive_message(
        QueueUrl=os.environ['PROCESSOR_QUEUE_URL'],
        MaxNumberOfMessages=1
    )
    
    assert 'Messages' in response
    received_message = json.loads(response['Messages'][0]['Body'])
    assert received_message == test_message

def test_lambda_handler(sqs_client, dynamodb_table, sqs_event):
    # 測試 Lambda 處理函數
    response = lambda_handler(sqs_event, None)
    assert response['statusCode'] == 200
    
    # 驗證消息是否被保存到 DynamoDB
    db_response = dynamodb_table.scan()
    assert len(db_response['Items']) == 1
    
    # 驗證消息是否被發送到處理隊列
    sqs_response = sqs_client.receive_message(
        QueueUrl=os.environ['PROCESSOR_QUEUE_URL'],
        MaxNumberOfMessages=1
    )
    assert 'Messages' in sqs_response 