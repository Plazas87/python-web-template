from uuid import UUID

import pytest

from {{ package_name }}.application.use_cases.login import LoginUseCase
from {{ package_name }}.domain.model.user import InvalidCredentialsError, User
from {{ package_name }}.domain.ports.repositories import UserRepository
from {{ package_name }}.domain.ports.services import PasswordHasher, TokenService


class FakeUserRepository(UserRepository):
    def __init__(self, users: list[User]) -> None:
        self.users = users

    def save(self, user: User) -> None:
        self.users.append(user)

    def find_by_id(self, id: UUID) -> User | None:
        return next((u for u in self.users if u.id == id), None)

    def find_by_email(self, email: str) -> User | None:
        return next((u for u in self.users if u.email == email), None)


class FakePasswordHasher(PasswordHasher):
    def hash(self, password: str) -> str:
        return f"hashed:{password}"

    def verify(self, password: str, password_hash: str) -> bool:
        return password_hash == f"hashed:{password}"


class FakeTokenService(TokenService):
    def issue_access_token(self, user_id: UUID) -> str:
        return f"token-for:{user_id}"

    def decode_access_token(self, token: str) -> UUID:
        raise NotImplementedError


def _existing_user() -> User:
    return User.create(email="jane@example.com", name="Jane", password_hash="hashed:s3cret123")


def test_login_issues_token_for_valid_credentials() -> None:
    user = _existing_user()
    use_case = LoginUseCase(
        repo=FakeUserRepository([user]),
        hasher=FakePasswordHasher(),
        tokens=FakeTokenService(),
    )

    token = use_case.execute(email="jane@example.com", password="s3cret123")

    assert token == f"token-for:{user.id}"


def test_login_rejects_wrong_password() -> None:
    use_case = LoginUseCase(
        repo=FakeUserRepository([_existing_user()]),
        hasher=FakePasswordHasher(),
        tokens=FakeTokenService(),
    )

    with pytest.raises(InvalidCredentialsError):
        use_case.execute(email="jane@example.com", password="wrong-password")


def test_login_rejects_unknown_email() -> None:
    use_case = LoginUseCase(
        repo=FakeUserRepository([]),
        hasher=FakePasswordHasher(),
        tokens=FakeTokenService(),
    )

    with pytest.raises(InvalidCredentialsError):
        use_case.execute(email="nobody@example.com", password="whatever")
