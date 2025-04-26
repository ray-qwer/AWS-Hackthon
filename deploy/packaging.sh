#!/bin/bash

# 創建臨時目錄
mkdir -p temp/lambda1
mkdir -p temp/lambda2

# 複製 Lambda 1 相關文件
cp app/lambda1_line.py temp/lambda1/
cp app/lambda1_classifier.py temp/lambda1/
cp -r app/utils temp/lambda1/

# 複製 Lambda 2 相關文件
cp app/lambda2.py temp/lambda2/
cp -r app/utils temp/lambda2/

# 安裝依賴到各自的目錄
pip install -r app/requirements.txt -t temp/lambda1/
pip install -r app/requirements.txt -t temp/lambda2/

# 創建 ZIP 文件
cd temp/lambda1
zip -r ../../lambda1.zip .
cd ../lambda2
zip -r ../../lambda2.zip .
cd ../..

# 清理臨時目錄
rm -rf temp

echo "Packaging completed. Created lambda1.zip and lambda2.zip" 