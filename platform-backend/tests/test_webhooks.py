"""Unit-Tests der Webhook-Verifikation/-Extraktion — ohne DB."""
import base64
import hashlib
import hmac

from app.routes.webhooks import (
    email_from_order,
    plan_code_from_order,
    verify_shopify_hmac,
)


def _sign(body: bytes, secret: str) -> str:
    return base64.b64encode(
        hmac.new(secret.encode(), body, hashlib.sha256).digest()
    ).decode()


def test_verify_valid_and_invalid():
    body = b'{"a":1}'
    secret = "s3cret"
    good = _sign(body, secret)
    assert verify_shopify_hmac(body, good, secret) is True
    assert verify_shopify_hmac(body, good, "wrong") is False
    assert verify_shopify_hmac(body, "AAAA", secret) is False
    assert verify_shopify_hmac(body, "", secret) is False
    assert verify_shopify_hmac(body, good, "") is False


def test_plan_code_from_order():
    order = {"line_items": [{"sku": "misc"}, {"sku": "PLAN-Pro"}]}
    assert plan_code_from_order(order) == "pro"
    assert plan_code_from_order({"line_items": []}) is None
    assert plan_code_from_order({}) is None


def test_email_from_order():
    assert email_from_order({"email": "a@b.ch"}) == "a@b.ch"
    assert email_from_order({"customer": {"email": "c@d.ch"}}) == "c@d.ch"
    assert email_from_order({}) is None
