from __future__ import annotations

from shared_backend.domain.current_user import AuthenticatedUserContext
from shared_backend.errors.custom_exceptions import AdminAccessRequiredError


def ensure_admin_user(current_user: AuthenticatedUserContext) -> AuthenticatedUserContext:
    if current_user.role != "admin":
        raise AdminAccessRequiredError()
    return current_user
