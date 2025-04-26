import json
import pytest
from unittest.mock import patch, MagicMock
from app.lambda1_line import lambda_handler, verify_signature

@pytest.fixture
def mock_event():
    return {
        'headers': {
            'x-line-signature': 'test_signature'
        },
        'body': json.dumps({
            'events': [
                {
                    'type': 'message',
                    'message': {
                        'type': 'text',
                        'id': 'test_message_id',
                        'text': 'Hello'
                    },
                    'source': {
                        'userId': 'test_user_id',
                        'type': 'user'
                    },
                    'timestamp': 1234567890
                }
            ]
        })
    }

@pytest.fixture
def mock_context():
    return MagicMock()

@patch('app.lambda1_line.sqs.send_message')
@patch('app.lambda1_line.verify_signature')
def test_lambda_handler_success(mock_verify, mock_send, mock_event, mock_context):
    # 設置模擬返回值
    mock_verify.return_value = True
    mock_send.return_value = {'MessageId': 'test_message_id'}
    
    # 調用處理函數
    response = lambda_handler(mock_event, mock_context)
    
    # 驗證結果
    assert response['statusCode'] == 200
    assert response['body'] == 'OK'
    mock_send.assert_called_once()

@patch('app.lambda1_line.verify_signature')
def test_lambda_handler_invalid_signature(mock_verify, mock_event, mock_context):
    # 設置模擬返回值
    mock_verify.return_value = False
    
    # 調用處理函數
    response = lambda_handler(mock_event, mock_context)
    
    # 驗證結果
    assert response['statusCode'] == 400
    assert response['body'] == 'Invalid signature'

@patch('app.lambda1_line.sqs.send_message')
@patch('app.lambda1_line.verify_signature')
def test_lambda_handler_exception(mock_verify, mock_send, mock_event, mock_context):
    # 設置模擬異常
    mock_verify.return_value = True
    mock_send.side_effect = Exception('Test error')
    
    # 調用處理函數
    response = lambda_handler(mock_event, mock_context)
    
    # 驗證結果
    assert response['statusCode'] == 500
    assert 'Test error' in response['body']

def test_verify_signature():
    # 測試簽名驗證
    body = 'test_body'
    signature = 'test_signature'
    
    with patch('app.lambda1_line.hmac.new') as mock_hmac:
        mock_hmac.return_value.digest.return_value = b'test_hash'
        with patch('app.lambda1_line.base64.b64encode') as mock_b64:
            mock_b64.return_value.decode.return_value = 'test_signature'
            
            result = verify_signature(body, signature)
            assert result is True 