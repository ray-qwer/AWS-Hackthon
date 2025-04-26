#!/usr/bin/env python3
import os
import sys
from typing import List, Dict

# 必需的環境變數
REQUIRED_ENV_VARS = {
    'CHANNEL_ACCESS_TOKEN': 'LINE Bot Channel Access Token',
    'CHANNEL_SECRET': 'LINE Bot Channel Secret',
    'PUBLIC_VOICE_API_KEY': 'Public Voice API Key',
    'GENERATED_IMAGES_BUCKET_NAME': 'Generated Images S3 Bucket Name',
    'REEL_S3_BUCKET_NAME': 'Reel S3 Bucket Name',
    'DYNAMODB_TABLE_NAME': 'DynamoDB Table Name',
    'SQS_QUEUE_URL': 'SQS Queue URL',
    'CLASSIFIER_QUEUE_URL': 'Classifier SQS Queue URL',
    'PROCESSOR_QUEUE_URL': 'Processor SQS Queue URL'
}

def validate_environment_variables() -> Dict[str, List[str]]:
    """驗證環境變數是否設置"""
    missing_vars = []
    invalid_vars = []
    
    for var, description in REQUIRED_ENV_VARS.items():
        value = os.getenv(var)
        
        if value is None:
            missing_vars.append(f"{var} ({description})")
        elif not value.strip():
            invalid_vars.append(f"{var} ({description})")
    
    return {
        'missing': missing_vars,
        'invalid': invalid_vars
    }

def main():
    """主函數"""
    results = validate_environment_variables()
    
    if results['missing'] or results['invalid']:
        print("環境變數驗證失敗：")
        
        if results['missing']:
            print("\n缺少以下環境變數：")
            for var in results['missing']:
                print(f"  - {var}")
        
        if results['invalid']:
            print("\n以下環境變數為空：")
            for var in results['invalid']:
                print(f"  - {var}")
        
        sys.exit(1)
    else:
        print("所有必需的環境變數都已正確設置。")
        sys.exit(0)

if __name__ == "__main__":
    main() 