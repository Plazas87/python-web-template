from uuid import UUID

import pytest

from {{ package_name }}.adapters.outbound.events.in_process_event_dispatcher import (
    InProcessEventDispatcher,
)
from {{ package_name }}.application.use_cases.register_user import RegisterUserUseCase
from {{ package_name }}.domain.model.pagination import Page, PageRequest
from {{ package_name }}.domain.model.role import Role
from {{ package_name }}.domain.model.user import DuplicateEmailError, User
from {{ package_name }}.domain.ports.repositories import RoleRepository, UserRepository
from {{ package_name }}.domain.ports.services import EmailService, PasswordHasher


class FakeUserRepository(UserRepository):
    def __init__(self) -> None:
        self.saved: list[User] = []

    def save(self, user: User) -> None:
        self.saved.append(user)

    def find_by_id(self, id: UUID) -> User | None:
        return next((u for u in self.saved if u.id == id), None)

    def find_by_email(self, email: str) -> User | None:
        return next((u for u in self.saved if u.email == email), None)

    def list_page(self, page_request: PageRequest) -> Page[User]:
        end = page_request.offset + page_request.page_size
        items = self.saved[page_request.offset : end]
        return Page(
            items=items,
            page=page_request.page,
            page_size=page_request.page_size,
            total=len(self.saved),
        )

    def count(self) -> int:
        return len(self.saved)


class FakeRoleRepository(RoleRepository):
    def __init__(self) -> None:
        self.saved: list[Role] = []

    def save(self, role: Role) -> None:
        self.saved.append(role)

    def find_by_name(self, name: str) -> Role | None:
        return next((r for r in self.saved if r.name == name), None)


class FakePasswordHasher(PasswordHasher):
    def hash(self, password: str) -> str:
        return f"hashed:{password}"

    def verify(self, password: str, password_hash: str) -> bool:
        return password_hash == f"hashed:{password}"


class FakeEmailService(EmailService):
    def __init__(self) -> None:
        self.sent_to: list[User] = []

    def send_welcome(self, user: User) -> None:
        self.sent_to.append(user)


def test_register_user_hashes_password_and_assigns_default_role() -> None:
    repo = FakeUserRepository()
    use_case = RegisterUserUseCase(
        repo=repo,
        role_repo=FakeRoleRepository(),
        hasher=FakePasswordHasher(),
        email_svc=FakeEmailService(),
        dispatcher=InProcessEventDispatcher(),
    )

    user = use_case.execute(email="jane@example.com", name="Jane", password="s3cret123")

    assert repo.saved == [user]
    assert user.password_hash == "hashed:s3cret123"
    assert [role.name for role in user.roles] == ["user"]


def test_register_user_rejects_duplicate_email() -> None:
    repo = FakeUserRepository()
    use_case = RegisterUserUseCase(
        repo=repo,
        role_repo=FakeRoleRepository(),
        hasher=FakePasswordHasher(),
        email_svc=FakeEmailService(),
        dispatcher=InProcessEventDispatcher(),
    )
    use_case.execute(email="jane@example.com", name="Jane", password="s3cret123")

    with pytest.raises(DuplicateEmailError):
        use_case.execute(email="jane@example.com", name="Jane again", password="other-pass")
