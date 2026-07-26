import logging

from {{ package_name }}.domain.model.user import User
from {{ package_name }}.domain.ports.services import EmailService

log = logging.getLogger(__name__)


class ConsoleEmailService(EmailService):
    # Default stub adapter — swap for a real provider by implementing EmailService
    # and wiring it in container.py; nothing else in the app changes.
    def send_welcome(self, user: User) -> None:
        log.info("email.sent", extra={"context": {"to": user.email, "template": "welcome"}})
