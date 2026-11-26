"""Unit tests for Item validation (no Flask or MySQL needed).
Run from the repo root: python -m unittest discover -s tests
The full API is tested end to end with scripts/test_api.sh against the running containers.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))
from validation import validate_item  # noqa: E402

VALID = {"name": "Rice 5kg", "quantity": 12, "unit": "bag", "reorderLevel": 3}


class ValidateItemTest(unittest.TestCase):
    def test_valid_item_is_cleaned(self):
        clean, error = validate_item({**VALID, "name": "  Rice 5kg "})
        self.assertIsNone(error)
        self.assertEqual(clean, VALID)

    def test_zero_is_allowed(self):
        self.assertIsNone(validate_item({**VALID, "quantity": 0, "reorderLevel": 0})[1])

    def test_rejects_bad_input(self):
        bad = [
            None,
            [],
            {**VALID, "name": " "},
            {**VALID, "name": "x" * 101},
            {**VALID, "unit": 5},
            {**VALID, "unit": "x" * 21},
            {**VALID, "quantity": -1},
            {**VALID, "quantity": 2.5},
            {**VALID, "quantity": "3"},
            {**VALID, "quantity": 2**32},
            {**VALID, "reorderLevel": True},
            {k: v for k, v in VALID.items() if k != "quantity"},
        ]
        for body in bad:
            with self.subTest(body=body):
                clean, error = validate_item(body)
                self.assertIsNone(clean)
                self.assertTrue(error)


if __name__ == "__main__":
    unittest.main()
