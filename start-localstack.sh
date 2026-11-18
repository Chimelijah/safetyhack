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
# The first run pulls the image and starts slowly, so poll instead of sleeping.
for _ in $(seq 1 60); do
  if curl -sf http://localhost:4566/_localstack/health; then
    echo
    exit 0
  fi
  sleep 2
done
echo "LocalStack did not become healthy within 2 minutes" >&2
exit 1
