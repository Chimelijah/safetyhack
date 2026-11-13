#!/bin/bash
docker rm -f localstack-demo 2>/dev/null || true
rm -f out1.json out2.json out3.json out4.json gate_lambda.zip
echo "cleaned up."
