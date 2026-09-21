from uuid import UUID

import pytest

from {{ package_name }}.application.use_cases.list_users import ListUsersUseCase
from {{ package_name }}.domain.model.role import Role
from {{ package_name }}.domain.model.user import User
from {{ package_name }}.domain.ports.policy import PermissionDeniedError, Policy
from {{ package_name }}.domain.ports.repositories import UserRepository


class FakeUserRepository(UserRepository):
    def __init__(self, users: list[User]) -> None:
        self.users = users

    def save(self, user: User) -> None:
        self.users.append(user)

    def find_by_id(self, id: UUID) -> User | None:
        return next((u for u in self.users if u.id == id), None)

    def find_by_email(self, email: str) -> User | None:
        return next((u for u in self.users if u.email == email), None)

    def list_all(self) -> list[User]:
        return list(self.users)


class AdminsOnlyPolicy(Policy):
    def can(self, actor: User, action: str, resource: object) -> bool:
        return actor.has_role("admin")


def test_admin_can_list_users() -> None:
    admin = User.create(email="admin@example.com", name="Admin", roles=[Role.create("admin")])
    other = User.create(email="jane@example.com", name="Jane")
    use_case = ListUsersUseCase(repo=FakeUserRepository([admin, other]), policy=AdminsOnlyPolicy())

    assert use_case.execute(admin) == [admin, other]


def test_non_admin_is_denied() -> None:
    plain_user = User.create(email="jane@example.com", name="Jane")
    use_case = ListUsersUseCase(repo=FakeUserRepository([plain_user]), policy=AdminsOnlyPolicy())

    with pytest.raises(PermissionDeniedError):
        use_case.execute(plain_user)
