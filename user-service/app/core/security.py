"""
Security helpers for password hashing and JWT-style bearer tokens.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from datetime import UTC, datetime, timedelta
from typing import Any

from app.core.config import settings
from app.schemas.user import UserRole


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def hash_password(password: str) -> str:
    """Hash a plaintext password with PBKDF2-HMAC-SHA256."""
    salt = secrets.token_bytes(16)
    derived = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        settings.password_hash_iterations,
    )
    return (
        f"pbkdf2_sha256${settings.password_hash_iterations}"
        f"${_b64url_encode(salt)}${_b64url_encode(derived)}"
    )


def verify_password(password: str, password_hash: str) -> bool:
    """Verify plaintext password against hash created by `hash_password`."""
    try:
        algorithm, iterations_s, salt_s, expected_hash_s = password_hash.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        iterations = int(iterations_s)
        salt = _b64url_decode(salt_s)
        expected = _b64url_decode(expected_hash_s)
    except Exception:
        return False

    actual = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        iterations,
    )
    return hmac.compare_digest(actual, expected)


def create_access_token(*, subject: str, email: str, role: UserRole) -> str:
    """Create a signed HS256 token with identity and role claims."""
    now = datetime.now(UTC)
    exp = now + timedelta(minutes=settings.auth_access_token_expire_minutes)

    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": subject,
        "email": email,
        "role": role.value,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
    }

    header_b64 = _b64url_encode(
        json.dumps(header, separators=(",", ":"), sort_keys=True).encode("utf-8")
    )
    payload_b64 = _b64url_encode(
        json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    )
    signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
    signature = hmac.new(
        settings.auth_secret_key.encode("utf-8"),
        signing_input,
        hashlib.sha256,
    ).digest()
    return f"{header_b64}.{payload_b64}.{_b64url_encode(signature)}"


def decode_access_token(token: str) -> dict[str, Any]:
    """
    Validate token signature and expiration; returns JWT payload.

    Raises:
        ValueError: if token is invalid or expired.
    """
    try:
        header_b64, payload_b64, signature_b64 = token.split(".", 2)
    except ValueError as exc:
        raise ValueError("Malformed token.") from exc

    signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
    expected_signature = hmac.new(
        settings.auth_secret_key.encode("utf-8"),
        signing_input,
        hashlib.sha256,
    ).digest()
    provided_signature = _b64url_decode(signature_b64)
    if not hmac.compare_digest(expected_signature, provided_signature):
        raise ValueError("Invalid token signature.")

    try:
        header = json.loads(_b64url_decode(header_b64))
        payload = json.loads(_b64url_decode(payload_b64))
    except Exception as exc:
        raise ValueError("Invalid token payload.") from exc

    if header.get("alg") != "HS256":
        raise ValueError("Unsupported token algorithm.")

    exp = payload.get("exp")
    if not isinstance(exp, int):
        raise ValueError("Token missing expiration.")
    if int(time.time()) >= exp:
        raise ValueError("Token expired.")
    if not payload.get("sub") or not payload.get("email") or not payload.get("role"):
        raise ValueError("Token missing required claims.")

    return payload
