import logging

from {{ package_name }}.container import Container

log = logging.getLogger(__name__)


def log_user_count_heartbeat(container: Container) -> None:
    # Example scheduled job: a background job has no FastAPI request to hang a
    # Depends(get_db_session) off, so it opens and closes its own session directly
    # from the container — the same way scripts/seed.py does.
    session = container.session_factory()
    try:
        count = container.count_users(session)
        log.info("scheduler.heartbeat", extra={"context": {"user_count": count}})
    finally:
        session.close()
