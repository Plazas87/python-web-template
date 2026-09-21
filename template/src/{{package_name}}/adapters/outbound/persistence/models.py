from datetime import datetime
from uuid import UUID

from sqlalchemy import JSON, Column, ForeignKey, String, Table
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from {{ package_name }}.domain.model.role import Role
from {{ package_name }}.domain.model.user import User


class Base(DeclarativeBase):
    pass


user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", ForeignKey("users.id"), primary_key=True),
    Column("role_id", ForeignKey("roles.id"), primary_key=True),
)


class RoleModel(Base):
    __tablename__ = "roles"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, index=True)

    @classmethod
    def from_domain(cls, role: Role) -> "RoleModel":
        return cls(id=role.id, name=role.name)

    def to_domain(self) -> Role:
        return Role(id=self.id, name=self.name)


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    password_hash: Mapped[str] = mapped_column(String(255), default="")
    roles: Mapped[list[RoleModel]] = relationship(secondary=user_roles)

    @classmethod
    def from_domain(cls, user: User) -> "UserModel":
        return cls(
            id=user.id,
            email=user.email,
            name=user.name,
            password_hash=user.password_hash,
            roles=[RoleModel.from_domain(role) for role in user.roles],
        )

    def to_domain(self) -> User:
        return User(
            id=self.id,
            email=self.email,
            name=self.name,
            password_hash=self.password_hash,
            roles=[role.to_domain() for role in self.roles],
        )


class AuditLogModel(Base):
    __tablename__ = "audit_log"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    event_name: Mapped[str] = mapped_column(String(100), index=True)
    payload: Mapped[dict[str, object]] = mapped_column(JSON)
    occurred_at: Mapped[datetime] = mapped_column(index=True)
