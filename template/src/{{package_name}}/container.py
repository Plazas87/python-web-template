from collections.abc import AsyncIterator
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from {{ package_name }}.adapters.outbound.external.console_email import ConsoleEmailService
from {{ package_name }}.adapters.outbound.persistence.repositories import (
    SqlAlchemyRoleRepository,
    SqlAlchemyUserRepository,
)
from {{ package_name }}.adapters.outbound.security.argon2_password_hasher import (
    Argon2PasswordHasher,
)
from {{ package_name }}.adapters.outbound.security.jwt_token_service import JwtTokenService
from {{ package_name }}.adapters.outbound.security.role_based_policy import RoleBasedPolicy
from {{ package_name }}.application.use_cases.create_user import CreateUserUseCase
from {{ package_name }}.application.use_cases.list_users import ListUsersUseCase
from {{ package_name }}.application.use_cases.login import LoginUseCase
from {{ package_name }}.application.use_cases.register_user import RegisterUserUseCase
from {{ package_name }}.config import Settings
from {{ package_name }}.domain.model.user import User
from {{ package_name }}.domain.ports.services import InvalidTokenError


@dataclass
class Container:
    """The composition root: every port is wired to its concrete adapter here, once."""

    session_factory: sessionmaker[Session]
    email_service: ConsoleEmailService
    password_hasher: Argon2PasswordHasher
    token_service: JwtTokenService
    policy: RoleBasedPolicy

    @classmethod
    def build(cls, settings: Settings) -> "Container":
        engine = create_engine(settings.database_url)
        return cls(
            session_factory=sessionmaker(bind=engine, expire_on_commit=False),
            email_service=ConsoleEmailService(),
            password_hasher=Argon2PasswordHasher(),
            token_service=JwtTokenService(
                secret_key=settings.secret_key,
                expires_minutes=settings.access_token_expires_minutes,
            ),
            policy=RoleBasedPolicy(),
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

    def register_user_use_case(self, session: Session) -> RegisterUserUseCase:
        return RegisterUserUseCase(
            repo=SqlAlchemyUserRepository(session),
            role_repo=SqlAlchemyRoleRepository(session),
            hasher=self.password_hasher,
            email_svc=self.email_service,
        )

    def login_use_case(self, session: Session) -> LoginUseCase:
        return LoginUseCase(
            repo=SqlAlchemyUserRepository(session),
            hasher=self.password_hasher,
            tokens=self.token_service,
        )

    def list_users_use_case(self, session: Session) -> ListUsersUseCase:
        return ListUsersUseCase(repo=SqlAlchemyUserRepository(session), policy=self.policy)

    def current_user(self, session: Session, token: str) -> User:
        user_id: UUID = self.token_service.decode_access_token(token)
        user = SqlAlchemyUserRepository(session).find_by_id(user_id)
        if user is None:
            raise InvalidTokenError("token subject no longer exists")
        return user
