from abc import ABC, abstractmethod
from uuid import UUID

from {{ package_name }}.domain.model.user import User


class EmailService(ABC):
    @abstractmethod
    def send_welcome(self, user: User) -> None: ...


class PasswordHasher(ABC):
    @abstractmethod
    def hash(self, password: str) -> str: ...

    @abstractmethod
    def verify(self, password: str, password_hash: str) -> bool: ...


class InvalidTokenError(Exception):
    pass


class TokenService(ABC):
    @abstractmethod
    def issue_access_token(self, user_id: UUID) -> str: ...

    @abstractmethod
    def decode_access_token(self, token: str) -> UUID:
        """Raise InvalidTokenError if the token is missing, malformed, or expired."""
        ...
