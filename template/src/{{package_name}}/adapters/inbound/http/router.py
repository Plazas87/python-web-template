from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from {{ package_name }}.adapters.inbound.http.schemas import CreateUserRequest, UserResponse
from {{ package_name }}.application.use_cases.create_user import CreateUserUseCase
from {{ package_name }}.container import Container

router = APIRouter()


def get_container(request: Request) -> Container:
    return request.app.state.container


def get_db_session(container: Container = Depends(get_container)) -> Session:
    yield from container.new_session()


def get_create_user_use_case(
    container: Container = Depends(get_container),
    session: Session = Depends(get_db_session),
) -> CreateUserUseCase:
    return container.create_user_use_case(session)


@router.post("/users", response_model=UserResponse)
async def create_user(
    request: CreateUserRequest,
    use_case: CreateUserUseCase = Depends(get_create_user_use_case),
) -> UserResponse:
    user = use_case.execute(request.email, request.name)
    return UserResponse.from_domain(user)
