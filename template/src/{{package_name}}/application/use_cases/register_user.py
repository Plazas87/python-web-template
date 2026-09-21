import logging

from {{ package_name }}.domain.events import UserCreated
from {{ package_name }}.domain.model.role import Role
from {{ package_name }}.domain.model.user import DuplicateEmailError, User
from {{ package_name }}.domain.ports.events import EventDispatcher
from {{ package_name }}.domain.ports.repositories import RoleRepository, UserRepository
from {{ package_name }}.domain.ports.services import EmailService, PasswordHasher

log = logging.getLogger(__name__)

DEFAULT_ROLE = "user"


class RegisterUserUseCase:
    def __init__(
        self,
        repo: UserRepository,
        role_repo: RoleRepository,
        hasher: PasswordHasher,
        email_svc: EmailService,
        dispatcher: EventDispatcher,
    ):
        self._repo = repo
        self._role_repo = role_repo
        self._hasher = hasher
        self._email = email_svc
        self._dispatcher = dispatcher

    def execute(self, email: str, name: str, password: str) -> User:
        log.info("use_case.started", extra={"context": {"action": "register_user"}})
        if self._repo.find_by_email(email.lower().strip()) is not None:
            raise DuplicateEmailError(f"Email already registered: {email}")

        role = self._role_repo.find_by_name(DEFAULT_ROLE)
        if role is None:
            role = Role.create(DEFAULT_ROLE)
            self._role_repo.save(role)

        user = User.create(
            email=email,
            name=name,
            password_hash=self._hasher.hash(password),
            roles=[role],
        )
        self._repo.save(user)
        self._dispatcher.dispatch(UserCreated(user_id=user.id, email=user.email))
        self._email.send_welcome(user)
        log.info("use_case.completed", extra={"context": {"user_id": str(user.id)}})
        return user
