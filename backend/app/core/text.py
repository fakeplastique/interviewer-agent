"""Sanitization helpers for user-supplied text that reaches LLM prompts."""

import re

# Control characters except \n and \t
_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b-\x1f\x7f]")


def sanitize_text(text: str, max_length: int) -> str:
    """Strip control characters and hard-cap length.

    Applied at the point of use (consumer handlers, prompt building) because
    Kafka payloads bypass the API-layer Pydantic validation.
    """
    return _CONTROL_CHARS.sub("", text)[:max_length].strip()
