"""A minimal "single safety gate" Lambda.

This is the one chokepoint every tool-run request passes through. It does
exactly three things, in this order, and nothing else:

  1. Look up the requested target in a DynamoDB scope table.
  2. Refuse (deny) unless that target is explicitly marked authorized=true.
     Unknown target == deny. There is no implicit allow.
  3. On an allow, return an argv LIST (never a shell string) for the caller
     to execute elsewhere — this function never runs the tool itself.

Every decision, allow or deny, is logged with the target and the reason, so
there is always an audit trail of what was authorized and why.
"""

import json
import logging
import os

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

TABLE_NAME = os.environ.get("SCOPE_TABLE", "scope")

# ALLOWED_TOOLS is a closed set. The caller requests a tool by NAME; the
# gate itself owns the real argv template. The caller can never inject
# arbitrary command text — it can only pick from this fixed menu.
ALLOWED_TOOLS = {
    "ping": ["ping", "-c", "3"],
    "dns-lookup": ["dig", "+short"],
}


def _dynamodb_table():
    endpoint_url = os.environ.get("AWS_ENDPOINT_URL")
    resource = boto3.resource("dynamodb", endpoint_url=endpoint_url)
    return resource.Table(TABLE_NAME)


def handler(event, context):
    target = (event.get("target") or "").strip()
    tool = (event.get("tool") or "").strip()

    if not target or not tool:
        logger.info("DENY reason=missing_field target=%r tool=%r", target, tool)
        return _deny("target and tool are both required")

    if tool not in ALLOWED_TOOLS:
        logger.info("DENY reason=unknown_tool target=%s tool=%s", target, tool)
        return _deny(f"unknown tool: {tool}")

    table = _dynamodb_table()
    item = table.get_item(Key={"target": target}).get("Item")

    if item is None:
        logger.info("DENY reason=not_in_scope target=%s tool=%s", target, tool)
        return _deny(f"{target} is not in the authorized scope table")

    if not item.get("authorized", False):
        logger.info("DENY reason=explicitly_unauthorized target=%s tool=%s", target, tool)
        return _deny(f"{target} is recorded but explicitly NOT authorized")

    argv = ALLOWED_TOOLS[tool] + [target]
    logger.info("ALLOW target=%s tool=%s argv=%s", target, tool, argv)
    return {
        "decision": "allow",
        "argv": argv,
        "target": target,
        "tool": tool,
    }


def _deny(reason):
    return {"decision": "deny", "reason": reason}


# Local smoke test without touching AWS at all: `python gate_lambda.py`
if __name__ == "__main__":
    print(json.dumps(handler({"target": "x", "tool": "ping"}, None), indent=2))
