# API 文檔

本文檔詳細說明了系統中各個組件的 API 接口和交互方式。

## LINE Bot Webhook

### 接收消息
- **URL**: `/webhook`
- **Method**: POST
- **Headers**:
  - `Content-Type`: application/json
  - `X-Line-Signature`: 簽名字符串
- **Body**: LINE 消息事件
- **Response**: 200 OK

### 消息格式
```json
{
    "events": [
        {
            "type": "message",
            "replyToken": "reply_token",
            "source": {
                "userId": "user_id",
                "type": "user"
            },
            "timestamp": 1234567890,
            "message": {
                "type": "text",
                "id": "message_id",
                "text": "用戶消息"
            }
        }
    ]
}
```

## Lambda 函數 API

### Lambda1-Line
- **觸發器**: API Gateway
- **輸入**: LINE Webhook 事件
- **輸出**: SQS 消息
- **環境變數**:
  - `CHANNEL_ACCESS_TOKEN`
  - `CHANNEL_SECRET`
  - `SQS_QUEUE_URL`

### Lambda1-Classifier
- **觸發器**: SQS
- **輸入**: SQS 消息
- **輸出**: DynamoDB 記錄 + SQS 消息
- **環境變數**:
  - `DYNAMODB_TABLE_NAME`
  - `CLASSIFIER_QUEUE_URL`

### Lambda2
- **觸發器**: SQS
- **輸入**: SQS 消息
- **輸出**: S3 文件
- **環境變數**:
  - `GENERATED_IMAGES_BUCKET_NAME`
  - `REEL_S3_BUCKET_NAME`
  - `PUBLIC_VOICE_API_KEY`

## DynamoDB 表結構

### Messages 表
```json
{
    "TableName": "Messages",
    "KeySchema": [
        {
            "AttributeName": "messageId",
            "KeyType": "HASH"
        },
        {
            "AttributeName": "timestamp",
            "KeyType": "RANGE"
        }
    ],
    "AttributeDefinitions": [
        {
            "AttributeName": "messageId",
            "AttributeType": "S"
        },
        {
            "AttributeName": "timestamp",
            "AttributeType": "N"
        }
    ]
}
```

## SQS 隊列

### LineQueue
- **用途**: 接收 LINE 消息
- **消息格式**:
```json
{
    "messageId": "string",
    "userId": "string",
    "text": "string",
    "timestamp": number
}
```

### ClassifierQueue
- **用途**: 傳遞分類後的消息
- **消息格式**:
```json
{
    "messageId": "string",
    "userId": "string",
    "text": "string",
    "classification": "string",
    "timestamp": number
}
```

### ProcessorQueue
- **用途**: 傳遞待處理的消息
- **消息格式**:
```json
{
    "messageId": "string",
    "userId": "string",
    "text": "string",
    "classification": "string",
    "processingType": "string",
    "timestamp": number
}
```

## S3 存儲桶

### GeneratedImagesBucket
- **用途**: 存儲生成的圖片
- **路徑格式**: `images/{userId}/{timestamp}.jpg`
- **權限**: 私有

### ReelS3Bucket
- **用途**: 存儲處理後的視頻
- **路徑格式**: `reels/{userId}/{timestamp}.mp4`
- **權限**: 私有

## 錯誤處理

### HTTP 狀態碼
- 200: 成功
- 400: 請求錯誤
- 401: 未授權
- 500: 服務器錯誤

### 錯誤響應格式
```json
{
    "error": {
        "code": "ERROR_CODE",
        "message": "錯誤描述",
        "details": {}
    }
}
```

## 安全考慮

1. **LINE 簽名驗證**
   - 所有 LINE Webhook 請求必須通過簽名驗證
   - 使用 Channel Secret 進行 HMAC-SHA256 驗證

2. **AWS IAM 權限**
   - 最小權限原則
   - 使用角色而非用戶憑證
   - 定期輪換憑證

3. **數據加密**
   - S3 存儲桶啟用服務器端加密
   - DynamoDB 表啟用加密
   - 傳輸層使用 TLS 1.2+

4. **訪問控制**
   - S3 存儲桶使用預簽名 URL
   - API Gateway 使用 API 密鑰
   - 實現速率限制 