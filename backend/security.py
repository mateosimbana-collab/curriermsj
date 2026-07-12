"""Shared security checks for the unified and legacy Flask applications."""
import hashlib
import hmac
import os
from functools import wraps

from flask import Response, request


def secrets_match(received: str | None, expected: str | None) -> bool:
    return bool(received and expected) and hmac.compare_digest(received, expected)


def verify_meta_signature(body: bytes, signature: str | None) -> bool:
    app_secret = os.getenv("META_APP_SECRET", "")
    if not app_secret or not signature:
        return False
    expected = "sha256=" + hmac.new(app_secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature, expected)


def require_legacy_auth(view):
    @wraps(view)
    def protected(*args, **kwargs):
        expected_user = os.getenv("LEGACY_DASHBOARD_USER", "")
        expected_password = os.getenv("LEGACY_DASHBOARD_PASSWORD", "")
        if not expected_user or len(expected_password) < 12:
            return Response("Legacy dashboard auth not configured", status=503)

        auth = request.authorization
        if not auth or not (
            secrets_match(auth.username, expected_user)
            and secrets_match(auth.password, expected_password)
        ):
            return Response(
                "Unauthorized",
                status=401,
                headers={"WWW-Authenticate": 'Basic realm="CurrierMsj Legacy"'},
            )
        return view(*args, **kwargs)

    return protected
