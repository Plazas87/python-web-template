import dataclasses
import logging
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from {{ package_name }}.adapters.outbound.persistence.models import AuditLogModel

log = logging.getLogger(__name__)


def _json_safe(value: object) -> object:
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    return value


class AuditLogConsumer:
    # Subscribes to domain events and writes a generic audit row (event name,
    # payload, timestamp) — works for any dataclass event, not just UserCreated.
    # Uses the same session/transaction as the use case that dispatched the
    # event, so the audit trail can never disagree with what actually committed.
    def __init__(self, session: Session):
        self._session = session

    def __call__(self, event: object) -> None:
        payload = {}
        if dataclasses.is_dataclass(event) and not isinstance(event, type):
            payload = {k: _json_safe(v) for k, v in dataclasses.asdict(event).items()}

        self._session.add(
            AuditLogModel(
                id=uuid4(),
                event_name=type(event).__name__,
                payload=payload,
                occurred_at=datetime.now(UTC),
            )
        )
        self._session.flush()
        log.info("audit_log.recorded", extra={"context": {"event": type(event).__name__}})
