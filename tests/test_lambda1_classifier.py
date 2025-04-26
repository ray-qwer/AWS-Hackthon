import os
import json
import pytest
import boto3
from moto import mock_dynamodb, mock_sqs
from unittest.mock import patch, MagicMock
from app.lambda1_classifier import (
    lambda_handler,
    classify_message,
    save_to_dynamodb,
    send_to_classifier_queue
)

@pytest.fixture
def mock_event():
    return {
        "Records": [{
            "body": json.dumps({
                "message": "Hello",
                "user_id": "test_user",
                "timestamp": "2024-03-21T12:00:00Z"
            })
        }]
    }

@pytest.fixture
def mock_context():
    class MockContext:
        def __init__(self):
            self.function_name = "test_function"
            self.aws_request_id = "test_request_id"
    return MockContext()

@pytest.fixture
def dynamodb_table(aws_credentials):
    with mock_dynamodb():
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.create_table(
            TableName=os.environ.get('DYNAMODB_TABLE', 'test-table'),
            KeySchema=[
                {'AttributeName': 'user_id', 'KeyType': 'HASH'},
                {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'user_id', 'AttributeType': 'S'},
                {'AttributeName': 'timestamp', 'AttributeType': 'S'}
            ],
            ProvisionedThroughput={'ReadCapacityUnits': 1, 'WriteCapacityUnits': 1}
        )
        yield table

@pytest.fixture
def sqs_queue(aws_credentials):
    with mock_sqs():
        sqs = boto3.resource('sqs')
        queue = sqs.create_queue(QueueName=os.environ.get('SQS_QUEUE_NAME', 'test-queue'))
        yield queue

def test_classify_message():
    # 測試問候語分類
    assert classify_message('你好') == 'greeting'
    assert classify_message('早安') == 'greeting'
    
    # 測試問題分類
    assert classify_message('請問如何...') == 'question'
    assert classify_message('為什麼...') == 'question'
    
    # 測試圖片分類
    assert classify_message('發送圖片') == 'image'
    assert classify_message('照片') == 'image'
    
    # 測試視頻分類
    assert classify_message('影片') == 'video'
    assert classify_message('視頻') == 'video'
    
    # 測試語音分類
    assert classify_message('語音') == 'voice'
    assert classify_message('聲音') == 'voice'
    
    # 測試默認分類
    assert classify_message('普通文本') == 'text'

@mock_dynamodb
@mock_sqs
def test_save_to_dynamodb(dynamodb_table, aws_credentials):
    message = {
        'messageId': 'test_message_id',
        'userId': 'test_user_id',
        'text': 'Hello',
        'timestamp': 1234567890
    }
    
    save_to_dynamodb(message)
    
    # 驗證數據是否已保存
    response = dynamodb_table.get_item(Key={'messageId': 'test_message_id'})
    saved_item = response['Item']
    assert saved_item['messageId'] == message['messageId']
    assert saved_item['userId'] == message['userId']
    assert saved_item['text'] == message['text']
    assert saved_item['timestamp'] == message['timestamp']

@mock_sqs
def test_send_to_classifier_queue(sqs_queue, aws_credentials):
    message = {
        'messageId': 'test_message_id',
        'userId': 'test_user_id',
        'text': 'Hello',
        'timestamp': 1234567890
    }
    
    with patch('app.lambda1_classifier.CLASSIFIER_QUEUE_URL', sqs_queue):
        send_to_classifier_queue(message)
    
    # 驗證消息是否已發送到隊列
    sqs = boto3.client('sqs')
    messages = sqs.receive_message(QueueUrl=sqs_queue)['Messages']
    assert len(messages) == 1
    received_message = json.loads(messages[0]['Body'])
    assert received_message == message

@mock_dynamodb
@mock_sqs
def test_lambda_handler_success(mock_event, mock_context, dynamodb_table, sqs_queue, aws_credentials):
    with patch('app.lambda1_classifier.CLASSIFIER_QUEUE_URL', sqs_queue):
        response = lambda_handler(mock_event, mock_context)
    
    # 驗證結果
    assert response['statusCode'] == 200
    assert 'successfully' in response['body']
    
    # 驗證數據是否已保存到 DynamoDB
    message_id = json.loads(mock_event['Records'][0]['body'])['messageId']
    response = dynamodb_table.get_item(Key={'messageId': message_id})
    assert 'Item' in response
    
    # 驗證消息是否已發送到 SQS
    sqs = boto3.client('sqs')
    messages = sqs.receive_message(QueueUrl=sqs_queue)['Messages']
    assert len(messages) == 1

@mock_dynamodb
@mock_sqs
def test_lambda_handler_exception(mock_event, mock_context, dynamodb_table, sqs_queue, aws_credentials):
    with patch('app.lambda1_classifier.CLASSIFIER_QUEUE_URL', sqs_queue):
        with patch('app.lambda1_classifier.save_to_dynamodb', side_effect=Exception('Test error')):
            response = lambda_handler(mock_event, mock_context)
    
    # 驗證結果
    assert response['statusCode'] == 500
    assert 'Test error' in response['body']

@mock_dynamodb
@mock_sqs
def test_classify_message(aws_credentials, dynamodb_table, sqs_queue, mock_event, mock_context):
    response = lambda_handler(mock_event, mock_context)
    assert response['statusCode'] == 200
    
    # Verify DynamoDB entry
    table = boto3.resource('dynamodb').Table(os.environ.get('DYNAMODB_TABLE', 'test-table'))
    items = table.scan()['Items']
    assert len(items) == 1
    assert items[0]['user_id'] == 'test_user'
    
    # Verify SQS message
    messages = sqs_queue.receive_messages(MaxNumberOfMessages=1)
    assert len(messages) == 1
    message_body = json.loads(messages[0].body)
    assert message_body['user_id'] == 'test_user'

@mock_dynamodb
def test_save_to_dynamodb(aws_credentials, dynamodb_table, mock_event):
    table = boto3.resource('dynamodb').Table(os.environ.get('DYNAMODB_TABLE', 'test-table'))
    event_body = json.loads(mock_event['Records'][0]['body'])
    
    table.put_item(Item={
        'user_id': event_body['user_id'],
        'timestamp': event_body['timestamp'],
        'message': event_body['message']
    })
    
    response = table.get_item(
        Key={
            'user_id': event_body['user_id'],
            'timestamp': event_body['timestamp']
        }
    )
    assert 'Item' in response
    assert response['Item']['message'] == 'Hello'

@mock_sqs
def test_send_to_classifier_queue(aws_credentials, sqs_queue, mock_event):
    sqs = boto3.client('sqs')
    queue_url = sqs_queue.url
    
    message_body = json.loads(mock_event['Records'][0]['body'])
    sqs.send_message(
        QueueUrl=queue_url,
        MessageBody=json.dumps(message_body)
    )
    
    messages = sqs_queue.receive_messages(MaxNumberOfMessages=1)
    assert len(messages) == 1
    received_body = json.loads(messages[0].body)
    assert received_body['user_id'] == 'test_user'
    assert received_body['message'] == 'Hello'

@mock_dynamodb
@mock_sqs
def test_lambda_handler_success(aws_credentials, dynamodb_table, sqs_queue, mock_event, mock_context):
    response = lambda_handler(mock_event, mock_context)
    assert response['statusCode'] == 200
    assert 'body' in response
    
    # Verify both DynamoDB and SQS operations
    table = boto3.resource('dynamodb').Table(os.environ.get('DYNAMODB_TABLE', 'test-table'))
    items = table.scan()['Items']
    assert len(items) == 1
    
    messages = sqs_queue.receive_messages(MaxNumberOfMessages=1)
    assert len(messages) == 1

@mock_dynamodb
@mock_sqs
def test_lambda_handler_exception(aws_credentials, dynamodb_table, sqs_queue, mock_event, mock_context):
    # Modify event to trigger an exception
    mock_event['Records'][0]['body'] = 'invalid_json'
    
    response = lambda_handler(mock_event, mock_context)
    assert response['statusCode'] == 500
    assert 'error' in json.loads(response['body']) 