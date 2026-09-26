"""Shared validation for all adapters and direct core calls."""
import math
from urllib.parse import urlsplit

from jsonschema import Draft202012Validator

TEXT = {"type": "string", "maxLength": 10000}
PRICE = {"type": "number", "minimum": 0, "maximum": 1e12}
CURRENCY = {"type": "string", "pattern": "^[A-Z]{3}$"}
PAGE_CONTENT = {
    "landing": {"subheadline": TEXT, "cta_text": TEXT},
    "optin": {"offer_description": TEXT, "incentive": TEXT},
    "sales": {"benefits": {"type": "array", "items": TEXT, "maxItems": 100}, "price": PRICE, "currency": CURRENCY},
    "checkout": {"product_name": TEXT, "price": PRICE, "currency": CURRENCY, "checkout_url": TEXT},
    "upsell": {"product_name": TEXT, "price": PRICE, "currency": CURRENCY, "checkout_url": TEXT},
    "thankyou": {"message": TEXT},
}

EMAILS = {"type": "array", "maxItems": 100, "items": {
    "type": "object", "additionalProperties": False,
    "properties": {"subject": TEXT, "body": TEXT, "delay_days": {"type": "integer", "minimum": 0, "maximum": 3650}},
    "required": ["subject", "body", "delay_days"],
}}


def validate(schema, value):
    def finite(item):
        if isinstance(item, float) and not math.isfinite(item):
            raise ValueError("القيم الرقمية يجب أن تكون محدودة")
        if isinstance(item, dict):
            for child in item.values():
                finite(child)
        elif isinstance(item, list):
            for child in item:
                finite(child)
    finite(value)
    errors = sorted(Draft202012Validator(schema).iter_errors(value), key=lambda e: str(list(e.path)))
    if errors:
        error = errors[0]
        path = ".".join(map(str, error.path)) or "arguments"
        raise ValueError(f"{path}: {error.message}")


def validate_content(page_type, content):
    validate({"type": "object", "properties": PAGE_CONTENT[page_type], "additionalProperties": False}, content)
    url = content.get("checkout_url")
    if url:
        try:
            parsed = urlsplit(url)
            valid = parsed.scheme == "https" and parsed.hostname and not parsed.username and not parsed.password
        except ValueError:
            valid = False
        if not valid or any(c.isspace() for c in url):
            raise ValueError("checkout_url يجب أن يكون رابط HTTPS صالحًا")
