from collections.abc import AsyncIterator
from dataclasses import dataclass

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from {{ package_name }}.adapters.outbound.external.console_email import ConsoleEmailService
from {{ package_name }}.adapters.outbound.persistence.repositories import SqlAlchemyUserRepository
from {{ package_name }}.application.use_cases.create_user import CreateUserUseCase
from {{ package_name }}.config import Settings


@dataclass
class Container:
    """The composition root: every port is wired to its concrete adapter here, once."""

    session_factory: sessionmaker[Session]
    email_service: ConsoleEmailService

    @classmethod
    def build(cls, settings: Settings) -> "Container":
        engine = create_engine(settings.database_url)
        return cls(
            session_factory=sessionmaker(bind=engine, expire_on_commit=False),
            email_service=ConsoleEmailService(),
        )

    async def new_session(self) -> AsyncIterator[Session]:
        # Async generator, not sync: FastAPI commits this after the response is
        # already sent either way, but a sync generator's commit runs in a
        # threadpool, widening the window for a client's next request to race it.
        session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def create_user_use_case(self, session: Session) -> CreateUserUseCase:
        repo = SqlAlchemyUserRepository(session)
        return CreateUserUseCase(repo=repo, email_svc=self.email_service)
