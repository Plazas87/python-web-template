from {{ package_name }}.adapters.outbound.persistence.repositories import SqlAlchemyUserRepository
from {{ package_name }}.config import settings
from {{ package_name }}.container import Container
from {{ package_name }}.domain.model.user import User


def main() -> None:
    container = Container.build(settings)
    session = container.session_factory()
    try:
        repo = SqlAlchemyUserRepository(session)
        repo.save(User.create(email="demo@example.com", name="Demo User"))
        session.commit()
    finally:
        session.close()


if __name__ == "__main__":
    main()
