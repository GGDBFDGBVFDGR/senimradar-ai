from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.rate_limit import RateLimiter


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
        response.headers["Cache-Control"] = "no-store"
        return response


class BodySizeLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_bytes: int) -> None:
        super().__init__(app)
        self.max_bytes = max_bytes

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.method not in {"POST", "PUT", "PATCH"}:
            return await call_next(request)
        raw_length = request.headers.get("content-length")
        if raw_length is None:
            return await call_next(request)
        try:
            length = int(raw_length)
        except ValueError:
            return JSONResponse(
                status_code=400,
                content={"status": "error", "code": "invalid_content_length"},
            )
        if length > self.max_bytes:
            return JSONResponse(
                status_code=413,
                content={"status": "error", "code": "payload_too_large"},
            )
        return await call_next(request)


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, limit: int, window_seconds: int = 60) -> None:
        super().__init__(app)
        self.limiter = RateLimiter(limit=limit, window_seconds=window_seconds)

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.method != "POST":
            return await call_next(request)
        host = request.client.host if request.client else "unknown"
        if not self.limiter.allow(host):
            return JSONResponse(
                status_code=429,
                content={"status": "error", "code": "rate_limited"},
            )
        return await call_next(request)
