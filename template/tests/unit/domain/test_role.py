import pytest

from {{ package_name }}.domain.model.role import Role


def test_create_role_normalizes_name() -> None:
    role = Role.create(" Admin ")
    assert role.name == "admin"


def test_create_role_rejects_empty_name() -> None:
    with pytest.raises(ValueError):
        Role.create("")
