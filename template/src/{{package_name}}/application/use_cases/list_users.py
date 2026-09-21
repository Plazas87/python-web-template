import logging

from {{ package_name }}.domain.model.pagination import Page, PageRequest
from {{ package_name }}.domain.model.user import User
from {{ package_name }}.domain.ports.policy import PermissionDeniedError, Policy
from {{ package_name }}.domain.ports.repositories import UserRepository

log = logging.getLogger(__name__)


class ListUsersUseCase:
    def __init__(self, repo: UserRepository, policy: Policy):
        self._repo = repo
        self._policy = policy

    def execute(self, actor: User, page_request: PageRequest) -> Page[User]:
        if not self._policy.can(actor, "list", User):
            raise PermissionDeniedError(f"User {actor.id} may not list users")
        return self._repo.list_page(page_request)
