from __future__ import annotations

from shared_backend.clients.auth_service_networking_client import get_required_auth_service_client
from shared_backend.domain.current_user import (
    AuthenticatedUserContext,
    authenticated_user_context_from_resolved_session,
)
from shared_backend.errors.custom_exceptions import AdminAccessRequiredError


def resolve_authenticated_user_context(*, session_token: str) -> AuthenticatedUserContext:
    resolved_session = get_required_auth_service_client().resolve_session(session_token=session_token)
    return authenticated_user_context_from_resolved_session(resolved_session)


def ensure_admin_user(current_user: AuthenticatedUserContext) -> AuthenticatedUserContext:
    if current_user.role != "admin":
        raise AdminAccessRequiredError()
    return current_user
