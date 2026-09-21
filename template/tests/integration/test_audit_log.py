import uuid

from fastapi.testclient import TestClient
from sqlalchemy import select

from {{ package_name }}.adapters.outbound.persistence.models import AuditLogModel
from {{ package_name }}.config import settings
from {{ package_name }}.container import Container
from {{ package_name }}.main import app


def _find_audit_log_entries(event_name: str) -> list[AuditLogModel]:
    container = Container.build(settings)
    session = container.session_factory()
    try:
        stmt = select(AuditLogModel).where(AuditLogModel.event_name == event_name)
        return list(session.scalars(stmt))
    finally:
        session.close()


def test_registering_a_user_writes_a_user_created_audit_log_entry() -> None:
    email = f"{uuid.uuid4()}@example.com"

    with TestClient(app) as client:
        response = client.post(
            "/auth/register",
            json={"email": email, "name": "Jane", "password": "s3cret123"},
        )
    user_id = response.json()["id"]

    entries = [e for e in _find_audit_log_entries("UserCreated") if e.payload.get("email") == email]

    assert len(entries) == 1
    assert entries[0].payload["user_id"] == user_id
