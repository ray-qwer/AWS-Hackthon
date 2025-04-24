# LINE Bot 測試模組 (test_linebot.py)

本測試模組用於驗證 LINE Bot 的基本功能和 API Gateway 整合，確保 LINE Bot 能夠正確處理和回應各種類型的訊息。

## 功能概述

`test_linebot.py` 包含以下測試功能：

1. **訊息處理測試**：模擬文字訊息和貼圖訊息的 webhook 事件
2. **安全驗證測試**：測試訊息簽名機制，確保訊息來源的安全性驗證
3. **API Gateway 整合測試**：測試 LINE Bot 到 API Gateway 的資料傳送流程
4. **環境變數驗證**：確保必要的環境變數正確設置

## 測試類別

### TestLineBot

主要測試類別，包含以下測試方法：

- `setUp()`: 驗證必要的環境變數是否正確設置，配置測試資料庫和儲存桶
- `generate_signature()`: 測試訊息簽名機制，確保訊息來源的安全性驗證
- `create_api_gateway_event()`: 創建模擬 API Gateway 事件，模擬 LINE 平台發送到 API Gateway 的請求
- `test_text_message()`: 測試文字訊息的接收和處理
- `test_sticker_message()`: 測試貼圖訊息的接收和處理，驗證 Bot 對貼圖的回應功能
- `test_invalid_signature()`: 測試無效簽名的情況，確保安全驗證機制正常運作
- `test_api_gateway_integration()`: 測試完整的 API Gateway 到 LINE Bot 的資料流程

## 環境設置

測試前需要設置以下環境變數：

- `CHANNEL_SECRET`: LINE Bot 的頻道密鑰
- `CHANNEL_ACCESS_TOKEN`: LINE Bot 的頻道訪問令牌

測試過程中會自動設置以下測試環境變數：

- `TABLE_NAME`: 設為 'test-table'
- `ASSET_BUCKET_NAME`: 設為 'test-asset-bucket'
- `OUTPUT_BUCKET_NAME`: 設為 'test-output-bucket'

## 如何執行測試

1. 確保已安裝所有必要的依賴項：
   ```bash
   pip install -r app/requirements.txt
   ```

2. 設置必要的環境變數：
   ```bash
   export CHANNEL_SECRET='your_channel_secret'
   export CHANNEL_ACCESS_TOKEN='your_channel_access_token'
   ```

3. 執行測試：
   ```bash
   python -m unittest tests/test_linebot.py
   ```

## 測試覆蓋範圍

- Lambda 處理函數的請求處理
- LINE Bot 訊息處理邏輯
- 安全簽名驗證機制
- API Gateway 事件處理
- 使用者資料庫操作

## 注意事項

- 測試使用 mock 對象模擬外部依賴，如 LINE API 和資料庫操作
- 測試不會實際發送請求到 LINE 平台或修改真實資料庫
- 確保在執行測試前已正確設置環境變數，否則測試將失敗