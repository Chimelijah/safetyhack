#!/usr/bin/env python3
"""Run a tool only if the safety gate allows it.

Usage:  ./run-with-gate.py [--dry-run] <tool> <target>
Example: ./run-with-gate.py ping 127.0.0.1

This is the "caller" side of the single-gate pattern. It never builds a
command itself. It sends the tool NAME and the target to the gate Lambda,
and it runs only the argv list the gate sends back.

Fail-closed: anything other than a well-formed {"decision": "allow", ...}
response (a deny, an invoke error, bad JSON, a wrong shape) means nothing runs.
"""

import json
import os
import subprocess
import sys
import tempfile

ENDPOINT = os.environ.get("GATE_ENDPOINT_URL", "http://localhost:4566")
FUNCTION = os.environ.get("GATE_FUNCTION_NAME", "safety-gate")


def ask_gate(tool, target):
    """Invoke the gate Lambda and return its decoded response, or None."""
    env = dict(os.environ)
    env.setdefault("AWS_ACCESS_KEY_ID", "test")          # LocalStack accepts any
    env.setdefault("AWS_SECRET_ACCESS_KEY", "test")
    env.setdefault("AWS_DEFAULT_REGION", "us-east-1")
    env["AWS_PAGER"] = ""
    payload = json.dumps({"tool": tool, "target": target})
    with tempfile.NamedTemporaryFile(suffix=".json") as out:
        # argv list, no shell: tool and target can't change the command line.
        cmd = ["aws", "--endpoint-url", ENDPOINT, "lambda", "invoke",
               "--function-name", FUNCTION,
               "--cli-binary-format", "raw-in-base64-out",
               "--payload", payload, out.name]
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"gate unreachable: {result.stderr.strip()}", file=sys.stderr)
            return None
        try:
            return json.load(open(out.name))
        except ValueError:
            print("gate returned something that is not JSON", file=sys.stderr)
            return None


def main(args):
    dry_run = "--dry-run" in args
    args = [a for a in args if a != "--dry-run"]
    if len(args) != 2:
        print(__doc__.strip().split("\n\n")[0], file=sys.stderr)
        return 2
    tool, target = args

    decision = ask_gate(tool, target)
    if not isinstance(decision, dict) or decision.get("decision") != "allow":
        reason = decision.get("reason") if isinstance(decision, dict) else None
        print(f"BLOCKED: {reason or 'no valid allow from the gate'}")
        return 1

    argv = decision.get("argv")
    if not (isinstance(argv, list) and argv and all(isinstance(a, str) for a in argv)):
        print("BLOCKED: gate said allow but sent no usable argv")
        return 1

    print(f"ALLOWED: running {argv}", flush=True)
    if dry_run:
        return 0
    return subprocess.run(argv).returncode   # list, no shell


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
