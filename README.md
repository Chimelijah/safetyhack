# Safety Gate Demo

A minimal single-safety-gate pattern using DynamoDB + Lambda. Every tool-run request passes through one Lambda that looks up the target in a DynamoDB scope table and denies unless the target is explicitly `authorized=true`. On allow, it returns an argv list (never a shell string) for the caller to execute elsewhere; the gate never runs the tool itself. Every decision is logged.

Everything is tested entirely on LocalStack. No real AWS account is needed.

## Prerequisites

- Docker
- AWS CLI v2

## Run order

1. Make the scripts executable:

   ```bash
   chmod +x *.sh
   ```

2. Start LocalStack:

   ```bash
   ./start-localstack.sh
   ```

   Note: if `DOCKER_HOST` is set to a podman socket, run `unset DOCKER_HOST` first.

3. Deploy the table, role, and Lambda:

   ```bash
   ./deploy.sh
   ```

4. Run the tests (allow, unknown target, explicitly unauthorized, disallowed tool):

   ```bash
   ./test.sh
   ```

5. Try a caller that obeys the gate (runs a command only if the gate allows it):

   ```bash
   aws --endpoint-url=http://localhost:4566 dynamodb put-item --table-name scope \
     --item '{"target": {"S": "127.0.0.1"}, "authorized": {"BOOL": true}}'
   ./run-with-gate.py ping 127.0.0.1                      # allowed, runs the ping
   ./run-with-gate.py ping unknown-host.evil.example      # blocked, nothing runs
   ./run-with-gate.py --dry-run ping 127.0.0.1            # shows the argv only
   ```

6. Clean up when done:

   ```bash
   ./cleanup.sh
   ```
