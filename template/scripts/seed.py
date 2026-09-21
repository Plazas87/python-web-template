from {{ package_name }}.adapters.outbound.persistence.repositories import (
    SqlAlchemyRoleRepository,
    SqlAlchemyUserRepository,
)
from {{ package_name }}.config import settings
from {{ package_name }}.container import Container
from {{ package_name }}.domain.model.role import Role
from {{ package_name }}.domain.model.user import User


def main() -> None:
    container = Container.build(settings)
    session = container.session_factory()
    try:
        user_repo = SqlAlchemyUserRepository(session)
        role_repo = SqlAlchemyRoleRepository(session)

        user_repo.save(User.create(email="demo@example.com", name="Demo User"))

        admin_role = role_repo.find_by_name("admin")
        if admin_role is None:
            admin_role = Role.create("admin")
            role_repo.save(admin_role)

        admin = container.register_user_use_case(session).execute(
            email="admin@example.com", name="Admin User", password="changeme123"
        )
        admin.roles.append(admin_role)
        user_repo.save(admin)

        session.commit()
    finally:
        session.close()


if __name__ == "__main__":
    main()
