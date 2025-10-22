"""Validation utilities."""

import re


def validate_email(email: str) -> str:
    """Validate an email address.

    Args:
        email: The email address to validate

    Returns:
        The validated email address

    Raises:
        ValueError: If the email is invalid
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        raise ValueError(f"Invalid email address: {email}")
    return email


def validate_username(username: str) -> str:
    """Validate a username.

    Args:
        username: The username to validate

    Returns:
        The validated username

    Raises:
        ValueError: If the username is invalid
    """
    if len(username) < 3:
        raise ValueError("Username must be at least 3 characters")
    if not username.isalnum():
        raise ValueError("Username must contain only letters and numbers")
    return username
