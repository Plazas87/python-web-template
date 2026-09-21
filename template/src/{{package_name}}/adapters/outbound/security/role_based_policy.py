from {{ package_name }}.domain.model.user import User
from {{ package_name }}.domain.ports.policy import Policy


class RoleBasedPolicy(Policy):
    def can(self, actor: User, action: str, resource: object) -> bool:
        if action == "list" and resource is User:
            return actor.has_role("admin")
        return False
