from collections.abc import AsyncIterator
from typing import cast

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from {{ package_name }}.container import Container
from {{ package_name }}.domain.model.user import User
from {{ package_name }}.domain.ports.services import InvalidTokenError

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_container(request: Request) -> Container:
    return cast(Container, request.app.state.container)


async def get_db_session(container: Container = Depends(get_container)) -> AsyncIterator[Session]:
    async for session in container.new_session():
        yield session


def get_current_user(
    token: str = Depends(oauth2_scheme),
    container: Container = Depends(get_container),
    session: Session = Depends(get_db_session),
) -> User:
    try:
        return container.current_user(session, token)
    except InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
