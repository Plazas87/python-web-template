from fastapi import APIRouter, Request, Response, status
from sqlalchemy import text

from {{ package_name }}.container import Container

router = APIRouter()


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready")
async def ready(request: Request, response: Response) -> dict[str, str]:
    container: Container = request.app.state.container
    session = container.session_factory()
    try:
        session.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "not ready"}
    finally:
        session.close()
