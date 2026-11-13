#!/bin/bash

export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test
export AWS_DEFAULT_REGION=us-east-1
ENDPOINT="http://localhost:4566"

echo "=== 1. authorized target -> should ALLOW ==="
aws --endpoint-url=$ENDPOINT lambda invoke --function-name safety-gate --cli-binary-format raw-in-base64-out --payload '{"target": "demo.example.internal", "tool": "ping"}' out1.json
cat out1.json; echo

echo ""
echo "=== 2. unknown target -> should DENY ==="
aws --endpoint-url=$ENDPOINT lambda invoke --function-name safety-gate --cli-binary-format raw-in-base64-out --payload '{"target": "unknown-host.evil.example", "tool": "ping"}' out2.json
cat out2.json; echo

echo ""
echo "=== 3. explicitly unauthorized target -> should DENY ==="
aws --endpoint-url=$ENDPOINT dynamodb put-item --table-name scope --item '{"target": {"S": "off-limits.example.internal"}, "authorized": {"BOOL": false}}'
aws --endpoint-url=$ENDPOINT lambda invoke --function-name safety-gate --cli-binary-format raw-in-base64-out --payload '{"target": "off-limits.example.internal", "tool": "ping"}' out3.json
cat out3.json; echo

echo ""
echo "=== 4. disallowed tool name -> should DENY ==="
aws --endpoint-url=$ENDPOINT lambda invoke --function-name safety-gate --cli-binary-format raw-in-base64-out --payload '{"target": "demo.example.internal", "tool": "rm -rf /"}' out4.json
cat out4.json; echo
