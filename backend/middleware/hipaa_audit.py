"""
GrokDent FL — HIPAA Audit Middleware
Logs every HTTP request to the ``audit_logs`` table for HIPAA compliance.
Skips health checks, static assets, and favicons to avoid noise.
"""

import logging
import time
from datetime import datetime, timezone

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from backend.database import SessionLocal
from backend.models.audit_log import AuditLog

logger = logging.getLogger(__name__)

# Paths that should NOT generate an audit row
SKIP_PATHS = {"/health", "/favicon.ico", "/openapi.json", "/docs", "/redoc"}
SKIP_PREFIXES = ("/static",)


class HIPAAAuditMiddleware(BaseHTTPMiddleware):
    """
    HIPAA-compliant audit trail middleware.

    For every non-skipped request, persists:
    - HTTP method + path (as ``action`` / ``resource_type``)
    - Authenticated user ID (extracted from the JWT ``sub`` claim if present)
    - Client IP address
    - User-Agent header
    - Response status code and latency
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        # Fast-skip for noisy endpoints
        path = request.url.path
        if path in SKIP_PATHS or any(path.startswith(p) for p in SKIP_PREFIXES):
            return await call_next(request)

        start = time.perf_counter()
        response: Response = await call_next(request)
        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)

        # Fire-and-forget audit write — must not slow down the response
        try:
            self._write_audit_log(request, response, elapsed_ms)
        except Exception as exc:
            logger.error("HIPAA audit write failed: %s", exc)

        return response

    # ------------------------------------------------------------------
    # Internal: persist a single audit row
    # ------------------------------------------------------------------
    @staticmethod
    def _write_audit_log(
        request: Request,
        response: Response,
        elapsed_ms: float,
    ) -> None:
        """Write an audit log entry in its own short-lived DB session."""
        # Extract user_id and clinic_id from JWT state (set by auth dependency)
        user_id = None
        clinic_id = None
        if hasattr(request.state, "user_id"):
            user_id = request.state.user_id
        if hasattr(request.state, "clinic_id"):
            clinic_id = request.state.clinic_id

        # If we still don't have a clinic_id, try to parse the JWT manually
        if not user_id:
            auth_header = request.headers.get("authorization", "")
            if auth_header.startswith("Bearer "):
                try:
                    from jose import jwt
                    from backend.config import settings

                    token = auth_header.split(" ", 1)[1]
                    payload = jwt.decode(
                        token,
                        settings.SECRET_KEY,
                        algorithms=[settings.JWT_ALGORITHM],
                    )
                    user_id = payload.get("sub")
                    clinic_id = payload.get("clinic_id")
                except Exception:
                    pass  # token invalid or expired — log without user info

        # Map HTTP method → audit action
        method_action_map = {
            "GET": "view",
            "POST": "create",
            "PUT": "update",
            "PATCH": "update",
            "DELETE": "delete",
        }
        action = method_action_map.get(request.method, "access")

        # Client IP (handle proxies)
        client_ip = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
        if not client_ip and request.client:
            client_ip = request.client.host

        db = SessionLocal()
        try:
            entry = AuditLog(
                clinic_id=clinic_id or "system",
                user_id=user_id,
                action=action,
                resource_type=request.url.path,
                resource_id=None,
                ip_address=client_ip,
                user_agent=request.headers.get("user-agent", ""),
                details={
                    "method": request.method,
                    "path": request.url.path,
                    "query": str(request.query_params),
                    "status_code": response.status_code,
                    "elapsed_ms": elapsed_ms,
                },
                timestamp=datetime.now(timezone.utc),
            )
            db.add(entry)
            db.commit()
        except Exception as exc:
            db.rollback()
            logger.error("Could not write audit log: %s", exc)
        finally:
            db.close()
