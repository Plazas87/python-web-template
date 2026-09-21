import logging

from {{ package_name }}.domain.model.user import InvalidCredentialsError
from {{ package_name }}.domain.ports.repositories import UserRepository
from {{ package_name }}.domain.ports.services import PasswordHasher, TokenService

log = logging.getLogger(__name__)


class LoginUseCase:
    def __init__(self, repo: UserRepository, hasher: PasswordHasher, tokens: TokenService):
        self._repo = repo
        self._hasher = hasher
        self._tokens = tokens

    def execute(self, email: str, password: str) -> str:
        log.info("use_case.started", extra={"context": {"action": "login"}})
        user = self._repo.find_by_email(email.lower().strip())
        if user is None or not self._hasher.verify(password, user.password_hash):
            raise InvalidCredentialsError("Invalid email or password")

        token = self._tokens.issue_access_token(user.id)
        log.info("use_case.completed", extra={"context": {"user_id": str(user.id)}})
        return token
