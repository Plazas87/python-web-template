from {{ package_name }}.adapters.outbound.security.role_based_policy import RoleBasedPolicy
from {{ package_name }}.domain.model.role import Role
from {{ package_name }}.domain.model.user import User


def test_admin_can_list_users() -> None:
    admin = User.create(email="admin@example.com", name="Admin", roles=[Role.create("admin")])
    assert RoleBasedPolicy().can(admin, "list", User) is True


def test_non_admin_cannot_list_users() -> None:
    plain_user = User.create(email="jane@example.com", name="Jane", roles=[Role.create("user")])
    assert RoleBasedPolicy().can(plain_user, "list", User) is False


def test_unknown_action_is_denied_by_default() -> None:
    admin = User.create(email="admin@example.com", name="Admin", roles=[Role.create("admin")])
    assert RoleBasedPolicy().can(admin, "delete-everything", User) is False
