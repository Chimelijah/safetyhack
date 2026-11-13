#!/bin/bash
set -e

export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test
export AWS_DEFAULT_REGION=us-east-1
ENDPOINT="http://localhost:4566"

echo "=== creating scope table ==="
aws --endpoint-url=$ENDPOINT dynamodb create-table --cli-input-json file://create-table.json

echo "=== seeding one authorized target ==="
aws --endpoint-url=$ENDPOINT dynamodb put-item --table-name scope --item '{"target": {"S": "demo.example.internal"}, "authorized": {"BOOL": true}}'

echo "=== creating IAM role ==="
aws --endpoint-url=$ENDPOINT iam create-role --role-name gate-lambda-role --assume-role-policy-document file://trust-policy.json

echo "=== zipping the Lambda ==="
rm -f gate_lambda.zip
zip -q gate_lambda.zip gate_lambda.py

echo "=== creating the Lambda function ==="
aws --endpoint-url=$ENDPOINT lambda create-function \
  --function-name safety-gate \
  --runtime python3.12 \
  --handler gate_lambda.handler \
  --zip-file fileb://gate_lambda.zip \
  --role arn:aws:iam::000000000000:role/gate-lambda-role \
  --environment "Variables={SCOPE_TABLE=scope,AWS_ENDPOINT_URL=http://localhost.localstack.cloud:4566}" \
  --timeout 10

echo "=== waiting for it to go active ==="
sleep 10
aws --endpoint-url=$ENDPOINT lambda get-function --function-name safety-gate --query "Configuration.State"

echo "=== done. Run ./test.sh to try it. ==="
