import json
import os
import pytest
from moto import mock_sqs
import boto3
import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lambda1_line import lambda_handler, send_to_classifier_queue

@pytest.fixture
def sqs_client():
    with mock_sqs():
        client = boto3.client('sqs', region_name='ap-northeast-1')
        queue_url = client.create_queue(QueueName='ClassifierQueue')['QueueUrl']
        os.environ['CLASSIFIER_QUEUE_URL'] = queue_url
        yield client

@pytest.fixture
def line_event():
    return {
        'headers': {
            'x-line-signature': 'test_signature'
        },
        'body': json.dumps({
            'events': [{
                'type': 'message',
                'replyToken': 'test_reply_token',
                'source': {
                    'userId': 'test_user_id'
                },
                'message': {
                    'type': 'text',
                    'text': 'Hello, World!'
                }
            }]
        })
    }

def test_lambda_handler_with_valid_signature(sqs_client, line_event):
    # 模擬有效的簽名驗證
    response = lambda_handler(line_event, None)
    assert response['statusCode'] == 200

def test_lambda_handler_with_invalid_signature(sqs_client, line_event):
    # 模擬無效的簽名
    line_event['headers']['x-line-signature'] = 'invalid_signature'
    response = lambda_handler(line_event, None)
    assert response['statusCode'] == 400

def test_send_to_classifier_queue(sqs_client):
    # 測試發送消息到分類隊列
    test_message = {
        'type': 'text',
        'user_id': 'test_user',
        'message': 'Hello, World!'
    }
    
    send_to_classifier_queue(test_message)
    
    # 驗證消息是否被發送到隊列
    response = sqs_client.receive_message(
        QueueUrl=os.environ['CLASSIFIER_QUEUE_URL'],
        MaxNumberOfMessages=1
    )
    
    assert 'Messages' in response
    received_message = json.loads(response['Messages'][0]['Body'])
    assert received_message == test_message 