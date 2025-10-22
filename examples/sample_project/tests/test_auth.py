"""Tests for authentication service."""

import pytest
from src.auth import AuthService
from src.models import User, Admin


def test_register_user():
    """Test registering a new user."""
    auth = AuthService()
    user = auth.register("Alice", "alice@example.com")

    assert isinstance(user, User)
    assert user.name == "Alice"
    assert user.email == "alice@example.com"


def test_register_duplicate_user():
    """Test that registering a duplicate user raises error."""
    auth = AuthService()
    auth.register("Alice", "alice@example.com")

    with pytest.raises(ValueError, match="already exists"):
        auth.register("Alice2", "alice@example.com")


def test_register_admin():
    """Test registering an admin user."""
    auth = AuthService()
    admin = auth.register_admin("Bob", "bob@example.com", ["read", "write"])

    assert isinstance(admin, Admin)
    assert admin.name == "Bob"
    assert admin.email == "bob@example.com"
    assert admin.permissions == ["read", "write"]


def test_get_user_exists():
    """Test getting a user that exists."""
    auth = AuthService()
    auth.register("Carol", "carol@example.com")

    user = auth.get_user("carol@example.com")
    assert user is not None
    assert user.name == "Carol"


def test_get_user_not_exists():
    """Test getting a user that doesn't exist."""
    auth = AuthService()
    user = auth.get_user("nobody@example.com")
    assert user is None


def test_get_admin():
    """Test getting an admin user."""
    auth = AuthService()
    auth.register_admin("Dave", "dave@example.com", ["read"])

    admin = auth.get_user("dave@example.com")
    assert isinstance(admin, Admin)
    assert admin.has_permission("read")
