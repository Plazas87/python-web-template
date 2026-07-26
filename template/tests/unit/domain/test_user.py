import pytest

from {{ package_name }}.domain.model.user import User


def test_create_user_normalizes_email() -> None:
    user = User.create(email=" Test@Example.com ", name=" Jane ")
    assert user.email == "test@example.com"
    assert user.name == "Jane"


def test_create_user_rejects_invalid_email() -> None:
    with pytest.raises(ValueError):
        User.create(email="not-an-email", name="Jane")
