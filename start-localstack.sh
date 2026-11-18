#!/bin/bash
set -e
SOCK="${DOCKER_HOST#unix://}"
SOCK="${SOCK:-/var/run/docker.sock}"
docker rm -f localstack-demo 2>/dev/null || true
docker run -d --name localstack-demo \
  -p 4566:4566 \
  -e SERVICES=dynamodb,lambda,iam,logs,sts \
  -v "$SOCK":/var/run/docker.sock \
  localstack/localstack:3.0
echo "waiting for LocalStack to become healthy..."
sleep 10
curl -s http://localhost:4566/_localstack/health
