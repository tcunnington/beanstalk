"""Short, URL-safe identifier generation."""

import secrets


def new_id(prefix: str = "") -> str:
    """Generate a short random identifier, optionally namespaced by a prefix."""
    token = secrets.token_hex(6)
    return f"{prefix}_{token}" if prefix else token
