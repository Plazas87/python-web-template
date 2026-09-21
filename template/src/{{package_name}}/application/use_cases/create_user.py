import logging

from {{ package_name }}.domain.events import UserCreated
from {{ package_name }}.domain.model.user import User
from {{ package_name }}.domain.ports.events import EventDispatcher
from {{ package_name }}.domain.ports.repositories import UserRepository
from {{ package_name }}.domain.ports.services import EmailService

log = logging.getLogger(__name__)


class CreateUserUseCase:
    def __init__(self, repo: UserRepository, email_svc: EmailService, dispatcher: EventDispatcher):
        self._repo = repo
        self._email = email_svc
        self._dispatcher = dispatcher

    def execute(self, email: str, name: str) -> User:
        log.info("use_case.started", extra={"context": {"action": "create_user"}})
        user = User.create(email, name)
        self._repo.save(user)
        self._dispatcher.dispatch(UserCreated(user_id=user.id, email=user.email))
        self._email.send_welcome(user)
        log.info("use_case.completed", extra={"context": {"user_id": str(user.id)}})
        return user
