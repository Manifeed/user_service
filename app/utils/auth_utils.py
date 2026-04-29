import secrets

from shared_backend.utils.auth_utils import (
    hash_password,
    hash_secret_token,
    verify_password,
)

API_KEY_VISIBLE_PREFIX_LENGTH = 12
API_KEY_TOKEN_BYTES = 36
API_KEY_PREFIX = "mk"


def build_key_prefix(api_key: str) -> str:
    return api_key[:API_KEY_VISIBLE_PREFIX_LENGTH]

def generate_api_key() -> str:
    return f"{API_KEY_PREFIX}_{secrets.token_urlsafe(API_KEY_TOKEN_BYTES)}"