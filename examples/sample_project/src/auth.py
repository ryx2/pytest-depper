"""Authentication service."""

from .models import User, Admin


class AuthService:
    """Handles user authentication."""

    def __init__(self):
        """Initialize the auth service."""
        self.users: dict[str, User] = {}

    def register(self, name: str, email: str) -> User:
        """Register a new user.

        Args:
            name: The user's name
            email: The user's email

        Returns:
            The newly created user

        Raises:
            ValueError: If user already exists
        """
        if email in self.users:
            raise ValueError(f"User with email {email} already exists")

        user = User(name, email)
        self.users[email] = user
        return user

    def register_admin(self, name: str, email: str, permissions: list[str]) -> Admin:
        """Register a new admin user.

        Args:
            name: The admin's name
            email: The admin's email
            permissions: List of permissions

        Returns:
            The newly created admin

        Raises:
            ValueError: If admin already exists
        """
        if email in self.users:
            raise ValueError(f"User with email {email} already exists")

        admin = Admin(name, email, permissions)
        self.users[email] = admin
        return admin

    def get_user(self, email: str) -> User | None:
        """Get a user by email.

        Args:
            email: The user's email

        Returns:
            The user if found, None otherwise
        """
        return self.users.get(email)
