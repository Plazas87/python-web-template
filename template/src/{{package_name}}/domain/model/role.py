from dataclasses import dataclass, field
from uuid import UUID, uuid4


@dataclass
class Role:
    id: UUID = field(default_factory=uuid4)
    name: str = ""

    @classmethod
    def create(cls, name: str) -> "Role":
        if not name:
            raise ValueError("Role name must not be empty")
        return cls(id=uuid4(), name=name.strip().lower())
