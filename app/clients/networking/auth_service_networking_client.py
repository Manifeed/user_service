from __future__ import annotations

from typing import Any

import httpx

from shared_backend.clients.service_http_client import (
    ServiceClientConfig,
    build_service_config,
    request_service as shared_request_service,
    require_service_client as shared_require_service_client,
)
from shared_backend.errors.app_error import AppError, UpstreamServiceError
from shared_backend.schemas.internal.service_schema import InternalResolvedSessionRead, InternalServiceHealthRead
from shared_backend.schemas.internal.auth_service_schema import InternalSessionTokenRequest


class AuthServiceNetworkingClient:
    def __init__(
        self,
        config: ServiceClientConfig,
        http_client: httpx.Client | None = None,
    ) -> None:
        self._config = config
        self._http_client = http_client

    @classmethod
    def from_env(cls) -> "AuthServiceNetworkingClient | None":
        config = build_service_config(
            base_url_env="AUTH_SERVICE_URL",
            timeout_env="AUTH_SERVICE_TIMEOUT_SECONDS",
            default_timeout_seconds=5.0,
            service_name="Auth",
        )
        if config is None:
            return None
        return cls(config)

    def resolve_session(self, *, session_token: str) -> InternalResolvedSessionRead:
        response = self._post(
            "/internal/auth/resolve-session",
            json={"payload": InternalSessionTokenRequest(session_token=session_token).model_dump(mode="json")},
        )
        return InternalResolvedSessionRead.model_validate(response.json())

    def read_internal_health(self) -> InternalServiceHealthRead:
        response = self._request("GET", "/internal/health", params=None, json=None)
        return InternalServiceHealthRead.model_validate(response.json())

    def _post(self, path: str, *, json: dict[str, Any]) -> httpx.Response:
        return self._request("POST", path, params=None, json=json)

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None,
        json: dict[str, Any] | None,
    ) -> httpx.Response:
        return shared_request_service(
            config=self._config,
            method=method,
            path=path,
            params=params,
            json=json,
            http_client=self._http_client,
            app_error_factory=AppError,
            upstream_error_factory=UpstreamServiceError,
        )


def get_auth_service_client() -> AuthServiceNetworkingClient | None:
    return AuthServiceNetworkingClient.from_env()


def get_required_auth_service_client() -> AuthServiceNetworkingClient:
    return shared_require_service_client(
        get_auth_service_client(),
        env_name="AUTH_SERVICE_URL",
        upstream_error_factory=UpstreamServiceError,
    )
