import uuid

from fastapi.testclient import TestClient

from {{ package_name }}.adapters.outbound.persistence.repositories import (
    SqlAlchemyRoleRepository,
    SqlAlchemyUserRepository,
)
from {{ package_name }}.config import settings
from {{ package_name }}.container import Container
from {{ package_name }}.domain.model.role import Role
from {{ package_name }}.main import app


def _promote_to_admin(email: str) -> None:
    # Registration only ever assigns the default "user" role; this slice has
    # no promote-user endpoint yet, so tests reach into the DB directly, the
    # same way scripts/seed.py does.
    container = Container.build(settings)
    session = container.session_factory()
    try:
        user_repo = SqlAlchemyUserRepository(session)
        role_repo = SqlAlchemyRoleRepository(session)
        user = user_repo.find_by_email(email)
        assert user is not None

        admin_role = role_repo.find_by_name("admin")
        if admin_role is None:
            admin_role = Role.create("admin")
            role_repo.save(admin_role)

        user.roles.append(admin_role)
        user_repo.save(user)
        session.commit()
    finally:
        session.close()


def _register_and_login(client: TestClient, email: str, password: str) -> str:
    client.post("/auth/register", json={"email": email, "name": "Test User", "password": password})
    response = client.post("/auth/login", data={"username": email, "password": password})
    token: str = response.json()["access_token"]
    return token


def test_admin_can_list_users() -> None:
    email = f"{uuid.uuid4()}@example.com"
    password = "s3cret123"

    with TestClient(app) as client:
        token = _register_and_login(client, email, password)
        _promote_to_admin(email)
        response = client.get("/users", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert any(user["email"] == email for user in response.json())


def test_non_admin_cannot_list_users() -> None:
    email = f"{uuid.uuid4()}@example.com"
    password = "s3cret123"

    with TestClient(app) as client:
        token = _register_and_login(client, email, password)
        response = client.get("/users", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 403


def test_list_users_requires_authentication() -> None:
    with TestClient(app) as client:
        response = client.get("/users")
    assert response.status_code == 401
