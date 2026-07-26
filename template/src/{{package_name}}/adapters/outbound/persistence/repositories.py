from uuid import UUID

from sqlalchemy.orm import Session

from {{ package_name }}.adapters.outbound.persistence.models import UserModel
from {{ package_name }}.domain.model.user import User
from {{ package_name }}.domain.ports.repositories import UserRepository


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
