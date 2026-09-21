import uuid

from fastapi.testclient import TestClient

from {{ package_name }}.main import app


def test_register_login_and_me_round_trip() -> None:
    email = f"{uuid.uuid4()}@example.com"
    password = "s3cret123"

    with TestClient(app) as client:
        register_response = client.post(
            "/auth/register",
            json={"email": email, "name": "Jane", "password": password},
        )
        assert register_response.status_code == 201
        assert register_response.json()["roles"] == ["user"]

        login_response = client.post(
            "/auth/login",
            data={"username": email, "password": password},
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        me_response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert me_response.status_code == 200
        assert me_response.json()["email"] == email


def test_login_rejects_wrong_password() -> None:
    email = f"{uuid.uuid4()}@example.com"

    with TestClient(app) as client:
        client.post(
            "/auth/register",
            json={"email": email, "name": "Jane", "password": "s3cret123"},
        )
        login_response = client.post(
            "/auth/login",
            data={"username": email, "password": "wrong-password"},
        )
    assert login_response.status_code == 401


def test_me_rejects_missing_token() -> None:
    with TestClient(app) as client:
        response = client.get("/auth/me")
    assert response.status_code == 401
