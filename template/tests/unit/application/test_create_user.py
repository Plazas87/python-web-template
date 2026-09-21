from uuid import UUID

from {{ package_name }}.adapters.outbound.events.in_process_event_dispatcher import (
    InProcessEventDispatcher,
)
from {{ package_name }}.application.use_cases.create_user import CreateUserUseCase
from {{ package_name }}.domain.events import UserCreated
from {{ package_name }}.domain.model.pagination import Page, PageRequest
from {{ package_name }}.domain.model.user import User
from {{ package_name }}.domain.ports.repositories import UserRepository
from {{ package_name }}.domain.ports.services import EmailService


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


class FakeEmailService(EmailService):
    def __init__(self) -> None:
        self.sent_to: list[User] = []

    def send_welcome(self, user: User) -> None:
        self.sent_to.append(user)


def test_create_user_saves_and_sends_welcome_email() -> None:
    repo = FakeUserRepository()
    email = FakeEmailService()
    dispatcher = InProcessEventDispatcher()
    published: list[UserCreated] = []
    dispatcher.subscribe(UserCreated, published.append)
    use_case = CreateUserUseCase(repo=repo, email_svc=email, dispatcher=dispatcher)

    user = use_case.execute(email="jane@example.com", name="Jane")

    assert repo.saved == [user]
    assert email.sent_to == [user]
    assert len(published) == 1
    assert published[0].user_id == user.id
    assert published[0].email == user.email
