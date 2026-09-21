from uuid import UUID

import pytest

from {{ package_name }}.application.use_cases.list_users import ListUsersUseCase
from {{ package_name }}.domain.model.pagination import Page, PageRequest
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

    def list_page(self, page_request: PageRequest) -> Page[User]:
        end = page_request.offset + page_request.page_size
        items = self.users[page_request.offset : end]
        return Page(
            items=items,
            page=page_request.page,
            page_size=page_request.page_size,
            total=len(self.users),
        )

    def count(self) -> int:
        return len(self.users)


class AdminsOnlyPolicy(Policy):
    def can(self, actor: User, action: str, resource: object) -> bool:
        return actor.has_role("admin")


def test_admin_can_list_users() -> None:
    admin = User.create(email="admin@example.com", name="Admin", roles=[Role.create("admin")])
    other = User.create(email="jane@example.com", name="Jane")
    use_case = ListUsersUseCase(repo=FakeUserRepository([admin, other]), policy=AdminsOnlyPolicy())

    result = use_case.execute(admin, PageRequest(page=1, page_size=20))

    assert result.items == [admin, other]
    assert result.total == 2
    assert result.total_pages == 1


def test_pagination_slices_results() -> None:
    admin = User.create(email="admin@example.com", name="Admin", roles=[Role.create("admin")])
    others = [User.create(email=f"user{i}@example.com", name=f"User {i}") for i in range(5)]
    repo = FakeUserRepository([admin, *others])
    use_case = ListUsersUseCase(repo=repo, policy=AdminsOnlyPolicy())

    page_1 = use_case.execute(admin, PageRequest(page=1, page_size=2))
    page_2 = use_case.execute(admin, PageRequest(page=2, page_size=2))

    assert page_1.items == [admin, others[0]]
    assert page_2.items == [others[1], others[2]]
    assert page_1.total == 6
    assert page_1.total_pages == 3


def test_non_admin_is_denied() -> None:
    plain_user = User.create(email="jane@example.com", name="Jane")
    use_case = ListUsersUseCase(repo=FakeUserRepository([plain_user]), policy=AdminsOnlyPolicy())

    with pytest.raises(PermissionDeniedError):
        use_case.execute(plain_user, PageRequest())
