import json
import os
import pytest
from moto import mock_s3
import boto3
import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lambda2 import lambda_handler, generate_content, synthesize_voice, handle_text_message, handle_image_message, handle_video_message, handle_audio_message

@pytest.fixture
def s3_client():
    with mock_s3():
        client = boto3.client('s3')
        yield client

# ... existing code ... 