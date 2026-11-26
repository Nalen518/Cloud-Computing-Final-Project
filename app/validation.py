"""Input validation for the Item entity (no Flask or database imports, so it unit-tests anywhere)."""

TEXT_LIMITS = {"name": 100, "unit": 20}  # match the VARCHAR sizes in db/init.sql
MAX_INT = 4294967295  # MySQL INT UNSIGNED


def validate_item(data):
    """Return (clean_fields, None) or (None, error_message)."""
    if not isinstance(data, dict):
        return None, "body must be a JSON object"
    clean = {}
    for field, limit in TEXT_LIMITS.items():
        value = data.get(field)
        if not isinstance(value, str) or not value.strip():
            return None, f"'{field}' is required and must be a non-empty string"
        if len(value.strip()) > limit:
            return None, f"'{field}' must be at most {limit} characters"
        clean[field] = value.strip()
    for field in ("quantity", "reorderLevel"):
        value = data.get(field)
        # bool is a subclass of int in Python, so reject it explicitly.
        if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= MAX_INT:
            return None, f"'{field}' is required and must be a whole number, 0 or more"
        clean[field] = value
    return clean, None
