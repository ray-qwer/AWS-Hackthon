# Next Steps for Project Restructuring

## [賽前可以先完成的]

### LINE Bot & API Gateway
- 設置 LINE Developer 帳號和 Channel
- 實作 webhook 接收使用者訊息
- 配置 API Gateway 處理 POST 請求

### Lambda 功能模組化

Lambda 修改成兩個。Lambda 1 負責串接前後端，並且連接一個 Nova 作為 agent 判斷要生成文字、音訊、影片。Lambda 2 負責連接後端各種模型，再回傳結果給 Lambda 1。

#### Lambda 1 (訊息判斷器)
需修改的現有檔案
- `template.yaml` - 更新 Lambda 配置
- `app/lambda_function.py`
- IAM 角色政策文件 - 新增存取 Nova 和 Lambda 2 的權限

主要功能：
- LINE Bot 訊息接收與回應
- Nova agent 整合與內容類型判斷
- Lambda 2 觸發與回應處理

需修改的現有檔案：
- `template.yaml` - 更新 Lambda 配置
  - 新增 Nova 相關環境變數
  - 設定與 Lambda 2 的觸發關係
- `app/lambda_function.py`
  - 實作 Nova agent 整合邏輯
  - 新增訊息類型判斷功能
  - 實作 Lambda 2 呼叫機制
- IAM 角色政策文件
  - 新增存取 Nova 的權限
  - 新增呼叫 Lambda 2 的權限


#### Lambda 2 (內容生成器)
主要功能：
- 接收 Lambda 1 的請求
- 根據請求類型調用對應模型
- 處理模型回應並格式化

需修改的現有檔案：
- `template.yaml` - 新增 Lambda 2 配置
  - 設定觸發器
  - 配置環境變數
- `app/lambda_function.py`
  - 實作請求處理邏輯
  - 實作模型調用機制
  - 實作回應格式化
- IAM 角色政策文件
  - 設定存取 Bedrock 的權限
  - 設定存取語音服務的權限
  - 設定存取影片服務的權限

Some Reference of Lamda using agent flow
https://github.com/aws-educate-tw/aws_educate_taylor_swift_workshop/tree/main


#### Bedrock Nova（文字生成）
- Knowledge Base資料
  - 採訪講稿（聖融已經切好其中一部，剩下轉文字檔）:共有5部，但時間來不及可以先搞定一步就好 
- Prompt Management
  - 偶像回覆的方式、口吻，這邊可以先搜集一些別人統整的偶像人設（伊芳有找一些了）

#### Musetalk（影像生成）
input 音訊＆短片
- 音訊得等橘子提供api
- 短片：
  - 先準備每個偶像幾部正臉個人短片，for example 每位偶像兩部10sec短片(打歌服、休閒服)



## [比賽當天才能執行的]
#### Bedrock Nova
- 設定Knowledge Base
  - 建立 S3 bucket 存放資料
  - 配置 Titan Embedding
  - 設置 OpenSearch 索引
- 實作 prompt engineering

#### 語音與影片處理
- 整合遊戲橘子語音 API
- 部署 MuseTalk 於 SageMaker
- 建立影片合成流程