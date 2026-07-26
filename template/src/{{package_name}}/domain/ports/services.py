from abc import ABC, abstractmethod

from {{ package_name }}.domain.model.user import User


class EmailService(ABC):
    @abstractmethod
    def send_welcome(self, user: User) -> None: ...
