from pydantic import BaseModel, EmailStr

from {{ package_name }}.domain.model.user import User


class CreateUserRequest(BaseModel):
    email: EmailStr
    name: str


class UserResponse(BaseModel):
    id: str
    email: str
    name: str

    @classmethod
    def from_domain(cls, user: User) -> "UserResponse":
        return cls(id=str(user.id), email=user.email, name=user.name)
