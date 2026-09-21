from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from {{ package_name }}.adapters.outbound.persistence.models import RoleModel, UserModel
from {{ package_name }}.domain.model.pagination import Page, PageRequest
from {{ package_name }}.domain.model.role import Role
from {{ package_name }}.domain.model.user import User
from {{ package_name }}.domain.ports.repositories import RoleRepository, UserRepository


class SqlAlchemyUserRepository(UserRepository):
    def __init__(self, session: Session):
        self._session = session

    def save(self, user: User) -> None:
        model = UserModel.from_domain(user)
        self._session.merge(model)
        self._session.flush()

    def find_by_id(self, id: UUID) -> User | None:
        model = self._session.get(UserModel, id)
        return model.to_domain() if model else None

    def find_by_email(self, email: str) -> User | None:
        model = self._session.scalar(select(UserModel).where(UserModel.email == email))
        return model.to_domain() if model else None

    def list_page(self, page_request: PageRequest) -> Page[User]:
        stmt = (
            select(UserModel)
            .order_by(UserModel.email)
            .offset(page_request.offset)
            .limit(page_request.page_size)
        )
        models = self._session.scalars(stmt)
        return Page(
            items=[model.to_domain() for model in models],
            page=page_request.page,
            page_size=page_request.page_size,
            total=self.count(),
        )

    def count(self) -> int:
        return self._session.scalar(select(func.count()).select_from(UserModel)) or 0


class SqlAlchemyRoleRepository(RoleRepository):
    def __init__(self, session: Session):
        self._session = session

    def save(self, role: Role) -> None:
        model = RoleModel.from_domain(role)
        self._session.merge(model)
        self._session.flush()

    def find_by_name(self, name: str) -> Role | None:
        model = self._session.scalar(select(RoleModel).where(RoleModel.name == name))
        return model.to_domain() if model else None
