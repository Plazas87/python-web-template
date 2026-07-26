from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID


@dataclass(frozen=True)
class UserCreated:
    user_id: UUID
    email: str
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))
