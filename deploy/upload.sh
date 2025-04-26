#!/bin/bash

# 檢查是否提供了 S3 存儲桶名稱
if [ -z "$1" ]; then
    echo "Usage: $0 <s3-bucket-name>"
    exit 1
fi

S3_BUCKET=$1

# 上傳 Lambda 包到 S3
aws s3 cp lambda1.zip s3://${S3_BUCKET}/lambda1.zip
aws s3 cp lambda2.zip s3://${S3_BUCKET}/lambda2.zip

echo "Uploaded lambda1.zip and lambda2.zip to s3://${S3_BUCKET}/" 