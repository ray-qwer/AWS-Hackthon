import json
import pytest
from unittest.mock import patch, MagicMock
from app.lambda2 import (
    lambda_handler,
    generate_text,
    generate_voice,
    process_video,
    save_to_s3
)
import boto3
import os
import requests

@pytest.fixture
def mock_event():
    return {
        'Records': [
            {
                'body': json.dumps({
                    'messageId': 'test_message_id',
                    'userId': 'test_user_id',
                    'text': '你好',
                    'classification': 'greeting',
                    'timestamp': 1234567890
                })
            }
        ]
    }

@pytest.fixture
def mock_context():
    return MagicMock()

@patch('app.lambda2.bedrock.invoke_model')
def test_generate_text(mock_invoke):
    # 設置模擬返回值
    mock_invoke.return_value = {
        'body': json.dumps({'completion': 'Hello!'})
    }
    
    # 測試文本生成
    result = generate_text('Hello')
    assert result == 'Hello!'
    mock_invoke.assert_called_once()

@patch('app.lambda2.requests.post')
def test_generate_voice(mock_post):
    # 設置模擬返回值
    mock_response = MagicMock()
    mock_response.json.return_value = {
        'media_url': 'https://example.com/voice.wav',
        'status': 'success'
    }
    mock_post.return_value = mock_response
    
    # 測試語音生成
    result = generate_voice('Hello')
    
    # 驗證結果
    assert result == 'https://example.com/voice.wav'
    mock_post.assert_called_once()
    
    # 驗證請求頭
    call_args = mock_post.call_args[1]
    assert 'Authorization' in call_args['headers']
    assert call_args['headers']['Authorization'] == f'Bearer {os.environ["PUBLIC_VOICE_API_KEY"]}'
    
    # 驗證請求體
    assert 'text' in call_args['json']
    assert call_args['json']['text'] == 'Hello'

@patch('app.lambda2.requests.post')
def test_generate_voice_error(mock_post):
    # 設置模擬錯誤
    mock_response = MagicMock()
    mock_response.json.return_value = {
        'status': 'error',
        'message': 'Invalid text'
    }
    mock_post.return_value = mock_response
    
    # 測試錯誤處理
    with pytest.raises(Exception) as exc_info:
        generate_voice('')
    assert 'Invalid text' in str(exc_info.value)

@patch('app.lambda2.requests.post')
def test_generate_voice_network_error(mock_post):
    # 設置網絡錯誤
    mock_post.side_effect = requests.exceptions.RequestException('Network error')
    
    # 測試網絡錯誤處理
    with pytest.raises(requests.exceptions.RequestException) as exc_info:
        generate_voice('Hello')
    assert 'Network error' in str(exc_info.value)

@patch('app.lambda2.requests.get')
@patch('app.lambda2.s3.put_object')
@patch('app.lambda2.requests.post')
def test_process_video(mock_post, mock_put, mock_get):
    # 設置模擬返回值
    mock_audio_response = MagicMock()
    mock_audio_response.content = b'test_audio'
    mock_get.return_value = mock_audio_response
    
    mock_musetalk_response = MagicMock()
    mock_musetalk_response.json.return_value = {'video_url': 'https://example.com/video.mp4'}
    mock_post.return_value = mock_musetalk_response
    
    # 測試視頻處理
    result = process_video('https://example.com/audio.wav')
    assert result == 'https://example.com/video.mp4'
    mock_get.assert_called_once()
    mock_put.assert_called_once()
    mock_post.assert_called_once()

def test_save_to_s3(s3_bucket):
    # 測試保存到 S3
    content = b'test_content'
    key = 'test/key'
    
    s3 = boto3.client('s3')
    result = save_to_s3(content, s3_bucket, key)
    
    # 驗證文件是否已保存
    response = s3.get_object(Bucket=s3_bucket, Key=key)
    assert response['Body'].read() == content
    assert result == f'https://{s3_bucket}.s3.amazonaws.com/{key}'

@patch('app.lambda2.generate_text')
@patch('app.lambda2.generate_voice')
@patch('app.lambda2.process_video')
@patch('app.lambda2.save_to_s3')
def test_lambda_handler_greeting(
    mock_save, mock_process, mock_voice, mock_text,
    mock_event, mock_context, s3_bucket, dynamodb_table
):
    # 設置模擬返回值
    mock_text.return_value = 'Hello!'
    mock_voice.return_value = 'https://example.com/voice.wav'
    mock_save.return_value = 'https://example.com/saved.mp3'
    
    # 調用處理函數
    response = lambda_handler(mock_event, mock_context)
    
    # 驗證結果
    assert response['statusCode'] == 200
    assert 'successfully' in response['body']
    mock_text.assert_called_once()
    mock_voice.assert_called_once()
    mock_save.assert_called_once()
    
    # 驗證 DynamoDB 記錄
    table = boto3.resource('dynamodb').Table(dynamodb_table.name)
    response = table.get_item(
        Key={
            'user_id': json.loads(mock_event['Records'][0]['body'])['userId'],
            'timestamp': json.loads(mock_event['Records'][0]['body'])['timestamp']
        }
    )
    assert 'Item' in response

@patch('app.lambda2.generate_text')
@patch('app.lambda2.generate_voice')
@patch('app.lambda2.process_video')
@patch('app.lambda2.save_to_s3')
def test_lambda_handler_question(
    mock_save, mock_process, mock_voice, mock_text,
    mock_event, mock_context, s3_bucket, dynamodb_table
):
    # 修改事件為問題類型
    mock_event['Records'][0]['body'] = json.dumps({
        'messageId': 'test_message_id',
        'userId': 'test_user_id',
        'text': '請問如何...',
        'classification': 'question',
        'timestamp': 1234567890
    })
    
    # 設置模擬返回值
    mock_text.return_value = 'Answer'
    mock_voice.return_value = 'https://example.com/voice.wav'
    mock_process.return_value = 'https://example.com/video.mp4'
    mock_save.return_value = 'https://example.com/saved.mp4'
    
    # 調用處理函數
    response = lambda_handler(mock_event, mock_context)
    
    # 驗證結果
    assert response['statusCode'] == 200
    assert 'successfully' in response['body']
    mock_text.assert_called_once()
    mock_voice.assert_called_once()
    mock_process.assert_called_once()
    mock_save.assert_called_once()
    
    # 驗證 DynamoDB 記錄
    table = boto3.resource('dynamodb').Table(dynamodb_table.name)
    response = table.get_item(
        Key={
            'user_id': json.loads(mock_event['Records'][0]['body'])['userId'],
            'timestamp': json.loads(mock_event['Records'][0]['body'])['timestamp']
        }
    )
    assert 'Item' in response

@patch('app.lambda2.generate_text')
@patch('app.lambda2.generate_voice')
@patch('app.lambda2.process_video')
@patch('app.lambda2.save_to_s3')
def test_lambda_handler_error(
    mock_save, mock_process, mock_voice, mock_text,
    mock_event, mock_context, s3_bucket, dynamodb_table
):
    # 設置模擬錯誤
    mock_text.side_effect = Exception('Test error')
    
    # 調用處理函數
    response = lambda_handler(mock_event, mock_context)
    
    # 驗證錯誤處理
    assert response['statusCode'] == 500
    assert 'error' in response['body']
    
    # 驗證 DynamoDB 記錄
    table = boto3.resource('dynamodb').Table(dynamodb_table.name)
    response = table.get_item(
        Key={
            'user_id': json.loads(mock_event['Records'][0]['body'])['userId'],
            'timestamp': json.loads(mock_event['Records'][0]['body'])['timestamp']
        }
    )
    assert 'Item' in response
    assert response['Item']['status'] == 'error' 