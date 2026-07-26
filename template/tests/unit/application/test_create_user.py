from uuid import UUID

from {{ package_name }}.application.use_cases.create_user import CreateUserUseCase
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


class FakeEmailService(EmailService):
    def __init__(self) -> None:
        self.sent_to: list[User] = []

    def send_welcome(self, user: User) -> None:
        self.sent_to.append(user)


def test_create_user_saves_and_sends_welcome_email() -> None:
    repo = FakeUserRepository()
    email = FakeEmailService()
    use_case = CreateUserUseCase(repo=repo, email_svc=email)

    user = use_case.execute(email="jane@example.com", name="Jane")

    assert repo.saved == [user]
    assert email.sent_to == [user]
