from uuid import UUID

from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from {{ package_name }}.domain.model.user import User


class Base(DeclarativeBase):
    pass


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))

    @classmethod
    def from_domain(cls, user: User) -> "UserModel":
        return cls(id=user.id, email=user.email, name=user.name)

    def to_domain(self) -> User:
        return User(id=self.id, email=self.email, name=self.name)
