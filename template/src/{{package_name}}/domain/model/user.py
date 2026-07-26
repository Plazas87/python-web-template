from dataclasses import dataclass, field
from uuid import UUID, uuid4


@dataclass
class User:
    id: UUID = field(default_factory=uuid4)
    email: str = ""
    name: str = ""

    @classmethod
    def create(cls, email: str, name: str) -> "User":
        if not email or "@" not in email:
            raise ValueError(f"Invalid email: {email}")
        return cls(id=uuid4(), email=email.lower().strip(), name=name.strip())
