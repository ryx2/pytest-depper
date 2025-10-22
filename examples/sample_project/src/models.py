"""User models."""

from .validators import validate_email


class User:
    """A user in the system."""

    def __init__(self, name: str, email: str):
        """Initialize a user.

        Args:
            name: The user's name
            email: The user's email address
        """
        self.name = name
        self.email = validate_email(email)

    def __repr__(self) -> str:
        return f"User(name={self.name!r}, email={self.email!r})"


class Admin(User):
    """An admin user with elevated privileges."""

    def __init__(self, name: str, email: str, permissions: list[str]):
        """Initialize an admin user.

        Args:
            name: The admin's name
            email: The admin's email address
            permissions: List of permission strings
        """
        super().__init__(name, email)
        self.permissions = permissions

    def has_permission(self, permission: str) -> bool:
        """Check if admin has a specific permission.

        Args:
            permission: The permission to check

        Returns:
            True if the admin has the permission
        """
        return permission in self.permissions
