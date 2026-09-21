from abc import ABC, abstractmethod

from {{ package_name }}.domain.model.user import User


class PermissionDeniedError(Exception):
    pass


class Policy(ABC):
    @abstractmethod
    def can(self, actor: User, action: str, resource: object) -> bool:
        """Business-rule authorization: can `actor` perform `action` on `resource`?

        Called from inside use cases, not just enforced as an HTTP route guard —
        an HTTP dependency only proves there's a valid session; it says nothing
        about whether *this* actor may do *this* thing, so any non-HTTP caller
        (a background job, a script, another adapter) must go through this too.
        """
        ...
