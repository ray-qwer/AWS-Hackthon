# 部署指南

本文檔提供了詳細的部署步驟和配置說明。

## 前置要求

1. **AWS 賬戶**
   - 具有適當權限的 IAM 用戶
   - 配置好的 AWS CLI

2. **LINE 開發者賬戶**
   - LINE Bot Channel
   - Channel Access Token
   - Channel Secret

3. **遊戲橘子 API**
   - API Key
   - API 訪問權限

## 部署步驟

### 1. 準備環境

```bash
# 安裝 AWS CLI
curl "https://awscli.amazonaws.com/AWSCLIV2.pkg" -o "AWSCLIV2.pkg"
sudo installer -pkg AWSCLIV2.pkg -target /

# 配置 AWS 憑證
aws configure
```

### 2. 更新配置

編輯 `deploy/parameters.json`，填入必要的參數：

```json
{
    "ChannelAccessToken": "your_channel_access_token",
    "ChannelSecret": "your_channel_secret",
    "PublicVoiceApiKey": "your_public_voice_api_key",
    "GeneratedImagesBucketName": "your_generated_images_bucket",
    "ReelS3BucketName": "your_reel_bucket",
    "DynamoDBTableName": "your_dynamodb_table"
}
```

### 3. 部署系統

```bash
cd deploy
chmod +x deploy.sh
./deploy.sh
```

### 4. 配置 LINE Bot

1. 登錄 LINE Developer Console
2. 選擇你的 Bot Channel
3. 設置 Webhook URL
   - Webhook URL 格式：`https://{api-id}.execute-api.{region}.amazonaws.com/prod/webhook`
4. 啟用 Webhook

## 環境變數配置

創建 `.env` 文件並填入以下內容：

```bash
# LINE Bot 配置
CHANNEL_ACCESS_TOKEN=your_channel_access_token
CHANNEL_SECRET=your_channel_secret

# AWS 配置
GENERATED_IMAGES_BUCKET_NAME=your_generated_images_bucket
REEL_S3_BUCKET_NAME=your_reel_bucket
DYNAMODB_TABLE_NAME=your_dynamodb_table
SQS_QUEUE_URL=your_sqs_queue_url
CLASSIFIER_QUEUE_URL=your_classifier_queue_url
PROCESSOR_QUEUE_URL=your_processor_queue_url

# 遊戲橘子 API 配置
PUBLIC_VOICE_API_KEY=your_public_voice_api_key
```

## 驗證部署

1. **檢查 CloudFormation 堆棧**
   ```bash
   aws cloudformation describe-stacks --stack-name chiikawa-ws
   ```

2. **檢查 Lambda 函數**
   ```bash
   aws lambda list-functions
   ```

3. **檢查 S3 存儲桶**
   ```bash
   aws s3 ls
   ```

4. **檢查 DynamoDB 表**
   ```bash
   aws dynamodb list-tables
   ```

5. **檢查 SQS 隊列**
   ```bash
   aws sqs list-queues
   ```

## 更新部署

如果需要更新部署：

1. 修改代碼
2. 更新 `template.yaml`（如果需要）
3. 運行部署腳本
   ```bash
   cd deploy
   ./deploy.sh
   ```

## 回滾部署

如果需要回滾到之前的版本：

1. 使用 CloudFormation 回滾
   ```bash
   aws cloudformation rollback-stack --stack-name chiikawa-ws
   ```

2. 或者手動刪除堆棧並重新部署
   ```bash
   aws cloudformation delete-stack --stack-name chiikawa-ws
   ```

## 清理資源

如果需要完全刪除部署：

1. 刪除 CloudFormation 堆棧
   ```bash
   aws cloudformation delete-stack --stack-name chiikawa-ws
   ```

2. 手動刪除 S3 存儲桶
   ```bash
   aws s3 rb s3://your-bucket-name --force
   ```

3. 手動刪除 DynamoDB 表
   ```bash
   aws dynamodb delete-table --table-name your-table-name
   ``` 