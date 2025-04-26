#!/bin/bash
set -e

# Configuration
STACK_NAME="chiikawa-ws"
REGION="ap-northeast-1"
CODE_BUCKET="${STACK_NAME}-code-${REGION}"
CODE_KEY="lambda-code.zip"
TEMPLATE_FILE="deploy/template.yaml"
PARAMS_FILE="deploy/parameters.json"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Function to check if bucket exists
check_bucket_exists() {
    aws s3api head-bucket --bucket "$1" --region "$REGION" 2>/dev/null
    return $?
}

# Function to create bucket with proper settings
create_bucket() {
    local bucket_name="$1"
    echo "Creating bucket: $bucket_name in region $REGION"
    if [ "$REGION" = "us-east-1" ]; then
        aws s3api create-bucket --bucket "$bucket_name" --region "$REGION"
    else
        aws s3api create-bucket --bucket "$bucket_name" \
            --region "$REGION" \
            --create-bucket-configuration LocationConstraint="$REGION"
    fi
    
    # Enable versioning
    aws s3api put-bucket-versioning \
        --bucket "$bucket_name" \
        --versioning-configuration Status=Enabled \
        --region "$REGION"
    
    echo "Waiting for bucket to be available..."
    aws s3api wait bucket-exists --bucket "$bucket_name" --region "$REGION"
}

# Ensure the code bucket exists
if ! check_bucket_exists "$CODE_BUCKET"; then
    create_bucket "$CODE_BUCKET"
fi

# Clean and create package directory
rm -rf "${ROOT_DIR}/package"
mkdir -p "${ROOT_DIR}/package"

# Install dependencies
cd "${ROOT_DIR}"
pip install -r requirements.txt -t package/

# Package Lambda functions
cd package
zip -r ../lambda-code.zip .
cd ..

# Add Lambda function files to the zip
zip -g lambda-code.zip app/*.py

# Upload to S3
aws s3 cp lambda-code.zip "s3://${CODE_BUCKET}/${CODE_KEY}" \
    --region "$REGION"

# Update parameters file with actual values
sed -i.bak \
    -e "s/CODE_BUCKET_PLACEHOLDER/${CODE_BUCKET}/g" \
    -e "s/CODE_KEY_PLACEHOLDER/${CODE_KEY}/g" \
    "$PARAMS_FILE"

# Deploy CloudFormation stack
echo "Deploying CloudFormation stack..."
aws cloudformation deploy \
    --template-file "$TEMPLATE_FILE" \
    --stack-name "$STACK_NAME" \
    --parameter-overrides file://"$PARAMS_FILE" \
    --capabilities CAPABILITY_NAMED_IAM \
    --region "$REGION"

# Clean up
rm -rf "${ROOT_DIR}/package" "${ROOT_DIR}/lambda-code.zip" "$PARAMS_FILE.bak"

echo "Deployment completed successfully!" 