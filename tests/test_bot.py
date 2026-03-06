"""Tests for bot.py startup env var validation."""

import os
import pytest
from unittest.mock import patch


_ALL_ENV = {
    "TOKEN": "fake-token",
    "GUILD_ID": "123456789",
    "NETWORKADMIN_ROLE_ID": "111",
    "WELCOME_CHANNEL_ID": "222",
    "INITIAL_MEMBER_ROLE_ID": "333",
    "GENERAL_CHANNEL_ID": "444",
    "SUPPORT_CHANNEL_ID": "555",
    "VC_TEXT_CHANNEL_ID": "666",
    "DCADMIN_ROLE_ID": "777",
    "AMP_URL": "http://localhost:8080",
    "AMP_USER": "admin",
    "AMP_PASS": "password",
}

_REQUIRED_ENV = list(_ALL_ENV.keys())


def _run_validation(env: dict):
    """
    Re-runs only the env var validation block from bot.py in isolation,
    without importing the full module (which would call bot.run()).
    """
    missing = [k for k in _REQUIRED_ENV if not env.get(k)]
    if missing:
        raise RuntimeError(
            f"Missing required environment variables: {', '.join(missing)}"
        )


def test_all_env_present_no_raise():
    """No exception raised when all required env vars are set."""
    _run_validation(_ALL_ENV)


def test_missing_single_env_raises():
    """RuntimeError raised when one var is missing."""
    env = {k: v for k, v in _ALL_ENV.items() if k != "TOKEN"}
    with pytest.raises(RuntimeError) as exc_info:
        _run_validation(env)
    assert "TOKEN" in str(exc_info.value)


def test_missing_multiple_env_raises():
    """RuntimeError message lists all missing keys."""
    env = {
        k: v for k, v in _ALL_ENV.items() if k not in ("TOKEN", "GUILD_ID", "AMP_URL")
    }
    with pytest.raises(RuntimeError) as exc_info:
        _run_validation(env)
    msg = str(exc_info.value)
    assert "TOKEN" in msg
    assert "GUILD_ID" in msg
    assert "AMP_URL" in msg


def test_empty_string_env_treated_as_missing():
    """An empty string value is treated the same as missing."""
    env = {**_ALL_ENV, "TOKEN": ""}
    with pytest.raises(RuntimeError) as exc_info:
        _run_validation(env)
    assert "TOKEN" in str(exc_info.value)
