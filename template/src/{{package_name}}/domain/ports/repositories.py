from abc import ABC, abstractmethod
from uuid import UUID

from {{ package_name }}.domain.model.user import User


class UserRepository(ABC):
    @abstractmethod
    def save(self, user: User) -> None: ...

    @abstractmethod
    def find_by_id(self, id: UUID) -> User | None: ...
