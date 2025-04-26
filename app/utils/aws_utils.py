import boto3
import os
from typing import Dict, Any

def get_dynamodb_client():
    """Get DynamoDB client with region configuration"""
    return boto3.client('dynamodb', region_name=os.getenv('AWS_REGION', 'ap-northeast-1'))

def get_s3_client():
    """Get S3 client with region configuration"""
    return boto3.client('s3', region_name=os.getenv('AWS_REGION', 'ap-northeast-1'))

def get_sqs_client():
    """Get SQS client with region configuration"""
    return boto3.client('sqs', region_name=os.getenv('AWS_REGION', 'ap-northeast-1'))

def get_dynamodb_resource():
    """Get DynamoDB resource with region configuration"""
    return boto3.resource('dynamodb', region_name=os.getenv('AWS_REGION', 'ap-northeast-1'))

def get_s3_resource():
    """Get S3 resource with region configuration"""
    return boto3.resource('s3', region_name=os.getenv('AWS_REGION', 'ap-northeast-1')) 