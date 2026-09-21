from abc import ABC, abstractmethod
from uuid import UUID

from {{ package_name }}.domain.model.role import Role
from {{ package_name }}.domain.model.user import User


class UserRepository(ABC):
    @abstractmethod
    def save(self, user: User) -> None: ...

    @abstractmethod
    def find_by_id(self, id: UUID) -> User | None: ...

    @abstractmethod
    def find_by_email(self, email: str) -> User | None: ...

    @abstractmethod
    def list_all(self) -> list[User]: ...


class RoleRepository(ABC):
    @abstractmethod
    def save(self, role: Role) -> None: ...

    @abstractmethod
    def find_by_name(self, name: str) -> Role | None: ...
