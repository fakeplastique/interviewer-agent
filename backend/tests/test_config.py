"""Settings validation tests."""

import pytest

from app.config import Settings

SECURE_KEY = "x" * 48


def test_production_rejects_default_secret_key():
    with pytest.raises(ValueError):
        Settings(_env_file=None, ENVIRONMENT="production")


def test_production_rejects_short_secret_key():
    with pytest.raises(ValueError):
        Settings(_env_file=None, ENVIRONMENT="production", SECRET_KEY="too-short")


def test_production_accepts_secure_secret_key():
    settings = Settings(_env_file=None, ENVIRONMENT="production", SECRET_KEY=SECURE_KEY)
    assert settings.SECRET_KEY == SECURE_KEY


def test_development_allows_default_secret_key():
    settings = Settings(_env_file=None)
    assert settings.ENVIRONMENT == "development"
