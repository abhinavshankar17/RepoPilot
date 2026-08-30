import hmac
import hashlib
import base64
import json
import time
from typing import Dict, Any, Optional
from app.core.config import settings
from app.core.logging import logger


class SecurityUtils:
    """JWT Token Generation, Verification, and Password Hashing Utilities."""

    @classmethod
    def b64_encode(cls, data: bytes) -> str:
        return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")

    @classmethod
    def b64_decode(cls, data: str) -> bytes:
        padding = "=" * (4 - (len(data) % 4))
        return base64.urlsafe_b64decode(data + padding)

    @classmethod
    def create_access_token(
        cls,
        user_id: str,
        username: str,
        role: str = "user",
        expires_in_seconds: int = 86400
    ) -> str:
        """Generates a signed JWT access token."""
        header = {"alg": "HS256", "typ": "JWT"}
        now = int(time.time())
        payload = {
            "sub": user_id,
            "username": username,
            "role": role,
            "iat": now,
            "exp": now + expires_in_seconds
        }

        header_b64 = cls.b64_encode(json.dumps(header).encode("utf-8"))
        payload_b64 = cls.b64_encode(json.dumps(payload).encode("utf-8"))

        signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
        signature = hmac.new(settings.JWT_SECRET.encode("utf-8"), signing_input, hashlib.sha256).digest()
        signature_b64 = cls.b64_encode(signature)

        return f"{header_b64}.{payload_b64}.{signature_b64}"

    @classmethod
    def verify_access_token(cls, token: str) -> Dict[str, Any]:
        """Decodes and verifies signature & expiration of JWT token."""
        try:
            parts = token.split(".")
            if len(parts) != 3:
                raise ValueError("Invalid JWT token format.")

            header_b64, payload_b64, signature_b64 = parts
            signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
            expected_signature = hmac.new(settings.JWT_SECRET.encode("utf-8"), signing_input, hashlib.sha256).digest()

            if not hmac.compare_digest(cls.b64_encode(expected_signature), signature_b64):
                raise ValueError("Invalid JWT signature.")

            payload = json.loads(cls.b64_decode(payload_b64).decode("utf-8"))

            if payload.get("exp", 0) < time.time():
                raise ValueError("JWT token has expired.")

            return payload
        except Exception as e:
            logger.warning(f"JWT verification failed: {e}")
            raise ValueError(f"Authentication failed: {str(e)}")

    @classmethod
    def sanitize_error_message(cls, message: str) -> str:
        """Sanitizes sensitive file paths, environment variables, and API keys from error messages."""
        clean_msg = str(message)
        if settings.OPENAI_API_KEY:
            clean_msg = clean_msg.replace(settings.OPENAI_API_KEY, "[REDACTED_API_KEY]")
        if settings.JWT_SECRET:
            clean_msg = clean_msg.replace(settings.JWT_SECRET, "[REDACTED_SECRET]")

        # Redact host paths
        clean_msg = clean_msg.replace(settings.STORAGE_DIR, "[STORAGE_ROOT]")
        clean_msg = clean_msg.replace(settings.VECTOR_STORE_DIR, "[VECTOR_ROOT]")
        return clean_msg
