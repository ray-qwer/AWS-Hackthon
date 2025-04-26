import os
import pytest
from dotenv import load_dotenv
from moto import mock_s3, mock_dynamodb
import boto3

@pytest.fixture(scope="session", autouse=True)
def load_env():
    """Load environment variables from .env.test file."""
    load_dotenv(".env.test")

@pytest.fixture(scope="session")
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "ap-northeast-1"

@pytest.fixture
def s3_bucket(aws_credentials):
    """Create a mock S3 bucket for testing."""
    with mock_s3():
        s3 = boto3.client('s3')
        bucket_name = os.environ.get('GENERATED_IMAGES_BUCKET_NAME', 'test-generated-images-bucket')
        s3.create_bucket(
            Bucket=bucket_name,
            CreateBucketConfiguration={'LocationConstraint': 'ap-northeast-1'}
        )
        yield bucket_name

@pytest.fixture
def reel_bucket(aws_credentials):
    """Create a mock S3 bucket for Reel videos."""
    with mock_s3():
        s3 = boto3.client('s3')
        bucket_name = os.environ.get('REEL_S3_BUCKET_NAME', 'test-reel-bucket')
        s3.create_bucket(
            Bucket=bucket_name,
            CreateBucketConfiguration={'LocationConstraint': 'ap-northeast-1'}
        )
        yield bucket_name

@pytest.fixture
def dynamodb_table(aws_credentials):
    """Create a mock DynamoDB table for testing."""
    with mock_dynamodb():
        dynamodb = boto3.resource('dynamodb')
        table_name = os.environ.get('DYNAMODB_TABLE_NAME', 'test-dynamodb-table')
        table = dynamodb.create_table(
            TableName=table_name,
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