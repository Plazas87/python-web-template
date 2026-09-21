from dataclasses import dataclass, field
from uuid import UUID, uuid4

from {{ package_name }}.domain.model.role import Role


class DuplicateEmailError(Exception):
    pass


class InvalidCredentialsError(Exception):
    pass


@dataclass
class User:
    id: UUID = field(default_factory=uuid4)
    email: str = ""
    name: str = ""
    password_hash: str = ""
    roles: list[Role] = field(default_factory=list)

    @classmethod
    def create(
        cls,
        email: str,
        name: str,
        password_hash: str = "",
        roles: list[Role] | None = None,
    ) -> "User":
        if not email or "@" not in email:
            raise ValueError(f"Invalid email: {email}")
        return cls(
            id=uuid4(),
            email=email.lower().strip(),
            name=name.strip(),
            password_hash=password_hash,
            roles=roles or [],
        )

    def has_role(self, name: str) -> bool:
        return any(role.name == name for role in self.roles)
