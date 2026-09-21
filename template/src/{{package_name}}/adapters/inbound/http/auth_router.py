from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from {{ package_name }}.adapters.inbound.http.dependencies import (
    get_container,
    get_current_user,
    get_db_session,
)
from {{ package_name }}.adapters.inbound.http.schemas import (
    RegisterUserRequest,
    TokenResponse,
    UserResponse,
)
from {{ package_name }}.application.use_cases.login import LoginUseCase
from {{ package_name }}.application.use_cases.register_user import RegisterUserUseCase
from {{ package_name }}.container import Container
from {{ package_name }}.domain.model.user import DuplicateEmailError, InvalidCredentialsError, User

router = APIRouter(prefix="/auth", tags=["auth"])


def get_register_user_use_case(
    container: Container = Depends(get_container),
    session: Session = Depends(get_db_session),
) -> RegisterUserUseCase:
    return container.register_user_use_case(session)


def get_login_use_case(
    container: Container = Depends(get_container),
    session: Session = Depends(get_db_session),
) -> LoginUseCase:
    return container.login_use_case(session)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterUserRequest,
    use_case: RegisterUserUseCase = Depends(get_register_user_use_case),
) -> UserResponse:
    try:
        user = use_case.execute(request.email, request.name, request.password)
    except DuplicateEmailError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return UserResponse.from_domain(user)


@router.post("/login", response_model=TokenResponse)
async def login(
    form: OAuth2PasswordRequestForm = Depends(),
    use_case: LoginUseCase = Depends(get_login_use_case),
) -> TokenResponse:
    try:
        token = use_case.execute(form.username, form.password)
    except InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse.from_domain(current_user)
