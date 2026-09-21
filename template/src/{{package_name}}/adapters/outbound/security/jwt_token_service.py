from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt

from {{ package_name }}.domain.ports.services import InvalidTokenError, TokenService


class JwtTokenService(TokenService):
    def __init__(self, secret_key: str, algorithm: str = "HS256", expires_minutes: int = 60):
        self._secret_key = secret_key
        self._algorithm = algorithm
        self._expires_minutes = expires_minutes

    def issue_access_token(self, user_id: UUID) -> str:
        now = datetime.now(UTC)
        payload = {
            "sub": str(user_id),
            "iat": now,
            "exp": now + timedelta(minutes=self._expires_minutes),
        }
        return jwt.encode(payload, self._secret_key, algorithm=self._algorithm)

    def decode_access_token(self, token: str) -> UUID:
        try:
            payload = jwt.decode(token, self._secret_key, algorithms=[self._algorithm])
            return UUID(payload["sub"])
        except (jwt.PyJWTError, KeyError, ValueError) as exc:
            raise InvalidTokenError("invalid or expired access token") from exc
