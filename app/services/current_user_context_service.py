from __future__ import annotations

from app.clients.networking.auth_service_networking_client import get_required_auth_service_client
from app.domain.current_user import AuthenticatedUserContext
from shared_backend.errors.custom_exceptions import AdminAccessRequiredError


def resolve_authenticated_user_context(*, session_token: str) -> AuthenticatedUserContext:
    resolved_session = get_required_auth_service_client().resolve_session(session_token=session_token)
    return AuthenticatedUserContext(
        user_id=resolved_session.user_id,
        email=resolved_session.email,
        role=resolved_session.role,
        is_active=resolved_session.is_active,
        api_access_enabled=resolved_session.api_access_enabled,
        session_expires_at=resolved_session.session_expires_at,
    )


def ensure_admin_user(current_user: AuthenticatedUserContext) -> AuthenticatedUserContext:
    if current_user.role != "admin":
        raise AdminAccessRequiredError()
    return current_user
