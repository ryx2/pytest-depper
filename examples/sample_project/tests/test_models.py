"""Tests for user models."""

import pytest
from src.models import User, Admin


def test_user_creation():
    """Test creating a user."""
    user = User("Alice", "alice@example.com")
    assert user.name == "Alice"
    assert user.email == "alice@example.com"


def test_user_with_invalid_email():
    """Test that invalid email raises error."""
    with pytest.raises(ValueError, match="Invalid email"):
        User("Bob", "not-an-email")


def test_admin_creation():
    """Test creating an admin user."""
    admin = Admin("Carol", "carol@example.com", ["read", "write"])
    assert admin.name == "Carol"
    assert admin.email == "carol@example.com"
    assert admin.permissions == ["read", "write"]


def test_admin_has_permission():
    """Test checking admin permissions."""
    admin = Admin("Dave", "dave@example.com", ["read", "write", "delete"])
    assert admin.has_permission("read")
    assert admin.has_permission("write")
    assert admin.has_permission("delete")
    assert not admin.has_permission("admin")
