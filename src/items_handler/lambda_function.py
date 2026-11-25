"""items-handler: one Lambda behind API Gateway (proxy integration) for the Item entity.

Routes by HTTP method and resource path:
  POST /items           create an item   -> 201
  GET  /items/{itemId}  read one item    -> 200 / 404
"""
import json
import os
import uuid
from datetime import datetime, timezone
from decimal import Decimal

_table = None


def table():
    # Created on first use so the module imports without AWS (local tests swap this out).
    global _table
    if _table is None:
        import boto3
        _table = boto3.resource("dynamodb").Table(os.environ["TABLE_NAME"])
    return _table


def response(status, body=None):
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json"},
        "body": "" if body is None else json.dumps(body, default=_json_number),
    }


def _json_number(value):
    # DynamoDB returns numbers as Decimal; quantities are whole numbers.
    if isinstance(value, Decimal):
        return int(value)
    raise TypeError(f"not JSON serialisable: {type(value).__name__}")


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def validate_item(data):
    """Return (clean_fields, None) or (None, error_message)."""
    if not isinstance(data, dict):
        return None, "body must be a JSON object"
    clean = {}
    for field in ("name", "unit"):
        value = data.get(field)
        if not isinstance(value, str) or not value.strip():
            return None, f"'{field}' is required and must be a non-empty string"
        clean[field] = value.strip()
    for field in ("quantity", "reorderLevel"):
        value = data.get(field)
        # bool is a subclass of int in Python, so reject it explicitly.
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            return None, f"'{field}' is required and must be a whole number, 0 or more"
        clean[field] = value
    return clean, None


def parse_body(event):
    try:
        return json.loads(event.get("body") or ""), None
    except json.JSONDecodeError:
        return None, "body must be valid JSON"


def create_item(event):
    data, error = parse_body(event)
    if error is None:
        data, error = validate_item(data)
    if error:
        return response(400, {"message": error})
    now = _now()
    item = {"itemId": str(uuid.uuid4()), **data, "createdAt": now, "updatedAt": now}
    table().put_item(Item=item)
    return response(201, item)


def get_item(item_id):
    item = table().get_item(Key={"itemId": item_id}).get("Item")
    if item is None:
        return response(404, {"message": f"item {item_id} not found"})
    return response(200, item)


def lambda_handler(event, context):
    method = event.get("httpMethod")
    resource = event.get("resource")
    item_id = (event.get("pathParameters") or {}).get("itemId")

    try:
        if resource == "/items" and method == "POST":
            return create_item(event)
        if resource == "/items/{itemId}" and method == "GET":
            return get_item(item_id)
        return response(405, {"message": f"{method} {resource} is not supported"})
    except Exception as exc:  # log the detail to CloudWatch, return a generic 500
        print(f"ERROR {method} {resource}: {exc!r}")
        return response(500, {"message": "internal error"})
