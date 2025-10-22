"""Tests for validation utilities."""

import pytest
from src.validators import validate_email, validate_username


def test_validate_email_valid():
    """Test validating a valid email."""
    assert validate_email("test@example.com") == "test@example.com"
    assert validate_email("user.name+tag@example.co.uk") == "user.name+tag@example.co.uk"


def test_validate_email_invalid():
    """Test validating invalid emails."""
    with pytest.raises(ValueError, match="Invalid email"):
        validate_email("not-an-email")

    with pytest.raises(ValueError, match="Invalid email"):
        validate_email("@example.com")

    with pytest.raises(ValueError, match="Invalid email"):
        validate_email("user@")


def test_validate_username_valid():
    """Test validating a valid username."""
    assert validate_username("alice123") == "alice123"
    assert validate_username("user") == "user"


def test_validate_username_too_short():
    """Test validating a username that's too short."""
    with pytest.raises(ValueError, match="at least 3 characters"):
        validate_username("ab")


def test_validate_username_invalid_chars():
    """Test validating a username with invalid characters."""
    with pytest.raises(ValueError, match="only letters and numbers"):
        validate_username("user-name")

    with pytest.raises(ValueError, match="only letters and numbers"):
        validate_username("user@123")
