"""API-key hashing and verification using Argon2."""

import secrets

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

_hasher = PasswordHasher()


def generate_api_key() -> str:
    """Generate a new, URL-safe agent API key (plaintext, shown to the operator once)."""
    return secrets.token_urlsafe(32)


def hash_api_key(api_key: str) -> str:
    """Return an Argon2 hash of an API key for storage."""
    return _hasher.hash(api_key)


def verify_api_key(api_key: str, key_hash: str) -> bool:
    """Verify a plaintext API key against a stored Argon2 hash."""
    try:
        return _hasher.verify(key_hash, api_key)
    except VerifyMismatchError:
        return False
