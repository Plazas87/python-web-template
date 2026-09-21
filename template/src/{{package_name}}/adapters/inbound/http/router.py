from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from {{ package_name }}.adapters.inbound.http.dependencies import (
    get_container,
    get_current_user,
    get_db_session,
)
from {{ package_name }}.adapters.inbound.http.schemas import CreateUserRequest, UserResponse
from {{ package_name }}.application.use_cases.create_user import CreateUserUseCase
from {{ package_name }}.application.use_cases.list_users import ListUsersUseCase
from {{ package_name }}.container import Container
from {{ package_name }}.domain.model.user import User
from {{ package_name }}.domain.ports.policy import PermissionDeniedError

router = APIRouter()


def get_create_user_use_case(
    container: Container = Depends(get_container),
    session: Session = Depends(get_db_session),
) -> CreateUserUseCase:
    return container.create_user_use_case(session)


def get_list_users_use_case(
    container: Container = Depends(get_container),
    session: Session = Depends(get_db_session),
) -> ListUsersUseCase:
    return container.list_users_use_case(session)


@router.post("/users", response_model=UserResponse)
async def create_user(
    request: CreateUserRequest,
    use_case: CreateUserUseCase = Depends(get_create_user_use_case),
) -> UserResponse:
    user = use_case.execute(request.email, request.name)
    return UserResponse.from_domain(user)


@router.get("/users", response_model=list[UserResponse])
async def list_users(
    actor: User = Depends(get_current_user),
    use_case: ListUsersUseCase = Depends(get_list_users_use_case),
) -> list[UserResponse]:
    # get_current_user only proves there's a valid session; the actual
    # "is admin allowed to list users" business rule is the use case's
    # Policy check below, so it also protects non-HTTP callers.
    try:
        users = use_case.execute(actor)
    except PermissionDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    return [UserResponse.from_domain(user) for user in users]
