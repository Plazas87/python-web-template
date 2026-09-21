from pydantic import BaseModel, EmailStr, Field

from {{ package_name }}.domain.model.user import User


class PageResponse[ItemT](BaseModel):
    # Reusable envelope for any paginated list endpoint — see GET /users for the
    # pattern: map domain.model.pagination.Page's items to a response schema,
    # carry page/page_size/total/total_pages through as-is.
    items: list[ItemT]
    page: int
    page_size: int
    total: int
    total_pages: int


class CreateUserRequest(BaseModel):
    email: EmailStr
    name: str


class RegisterUserRequest(BaseModel):
    email: EmailStr
    name: str
    password: str = Field(min_length=8)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    roles: list[str] = []

    @classmethod
    def from_domain(cls, user: User) -> "UserResponse":
        return cls(
            id=str(user.id),
            email=user.email,
            name=user.name,
            roles=[role.name for role in user.roles],
        )
