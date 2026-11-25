"""Local tests for items-handler with an in-memory fake table (no AWS needed).
Run from the repo root: python -m unittest discover -s tests
"""
import json
import os
import sys
import unittest
from decimal import Decimal

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "items_handler"))
import lambda_function as h  # noqa: E402


class FakeTable:
    def __init__(self):
        self.items = {}

    def put_item(self, Item):
        # Store numbers as Decimal, like DynamoDB returns them.
        self.items[Item["itemId"]] = {k: Decimal(v) if isinstance(v, int) else v for k, v in Item.items()}

    def get_item(self, Key):
        item = self.items.get(Key["itemId"])
        return {"Item": dict(item)} if item else {}


def event(method, resource, body=None, item_id=None):
    return {
        "httpMethod": method,
        "resource": resource,
        "pathParameters": {"itemId": item_id} if item_id else None,
        "body": None if body is None else json.dumps(body),
    }


VALID = {"name": "Rice 5kg", "quantity": 12, "unit": "bag", "reorderLevel": 3}


class ItemsHandlerTest(unittest.TestCase):
    def setUp(self):
        h._table = FakeTable()

    def call(self, *args, **kwargs):
        res = h.lambda_handler(event(*args, **kwargs), None)
        return res["statusCode"], json.loads(res["body"]) if res["body"] else None

    def test_create_then_read(self):
        status, created = self.call("POST", "/items", VALID)
        self.assertEqual(status, 201)
        self.assertEqual(created["quantity"], 12)
        self.assertTrue(created["itemId"] and created["createdAt"] == created["updatedAt"])

        status, read = self.call("GET", "/items/{itemId}", item_id=created["itemId"])
        self.assertEqual(status, 200)
        self.assertEqual(read, created)  # Decimal comes back as a whole number

    def test_read_unknown_is_404(self):
        self.assertEqual(self.call("GET", "/items/{itemId}", item_id="nope")[0], 404)

    def test_create_rejects_bad_input(self):
        bad = [
            None,
            {**VALID, "name": " "},
            {**VALID, "unit": 5},
            {**VALID, "quantity": -1},
            {**VALID, "quantity": 2.5},
            {**VALID, "reorderLevel": True},
            {k: v for k, v in VALID.items() if k != "quantity"},
        ]
        for body in bad:
            with self.subTest(body=body):
                self.assertEqual(self.call("POST", "/items", body)[0], 400)

    def test_invalid_json_is_400(self):
        res = h.lambda_handler({"httpMethod": "POST", "resource": "/items", "body": "{oops"}, None)
        self.assertEqual(res["statusCode"], 400)

    def test_unsupported_route_is_405(self):
        self.assertEqual(self.call("PATCH", "/items")[0], 405)


if __name__ == "__main__":
    unittest.main()
