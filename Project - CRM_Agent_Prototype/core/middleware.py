# 필요한 모듈들을 임포트합니다.
import logging
import re
import time
from typing import Callable, Dict, List, Optional

from fastapi import Request, Response
from fastapi.responses import Response as FastAPIResponse
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Histogram,
    Info,
    generate_latest,
)
from starlette.middleware.base import BaseHTTPMiddleware

from core.exceptions import SecurityException
from core.settings import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

# Enable debug logging
if settings.DEBUG:
    logger.setLevel(logging.DEBUG)

# Prometheus 메트릭 정의
REQUEST_COUNT = Counter(
    "http_requests_total", "Total HTTP requests count", ["method", "endpoint", "status"]
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds", "HTTP request latency", ["method", "endpoint"]
)

API_ERROR_COUNT = Counter("api_errors_total", "Total API error count", ["error_type"])

API_INFO = Info("api_info", "API information")
API_INFO.info({"version": settings.VERSION, "environment": settings.ENVIRONMENT})


class SecurityMiddleware(BaseHTTPMiddleware):
    """보안 검사를 수행하는 미들웨어입니다."""

    def __init__(self, app):
        super().__init__(app)
        self._blocked_ips: Dict[str, float] = {}
        self._ip_rate_limits: Dict[str, List[float]] = {}
        self._suspicious_patterns = (
            [
                r"(?i)(union.*from|select.*from|insert.*into|update.*set|delete.*from|drop.*table)",
                r"<[^>]*script.*?>.*?</script.*?>",
                r"javascript\s*:",
                r"onload\s*=",
                r"onerror\s*=",
                r"/etc/passwd",
                r"\.\./",
                r"\{\{.*?\}\}",
                r"\$\{.*?\}",
            ]
            if not settings.DEBUG
            else []
        )  # Debug mode에서는 패턴 검사 비활성화

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client_ip = self._get_client_ip(request)
        start_time = time.time()

        try:
            # Allow Swagger UI and OpenAPI endpoints in debug mode
            if settings.DEBUG and request.url.path in [
                "/docs",
                "/openapi.json",
                "/redoc",
            ]:
                response = await call_next(request)
                self._add_debug_security_headers(response)
                return response

            # Debug mode logging
            if settings.DEBUG:
                logger.debug(
                    f"[SecurityMiddleware] Processing request from {client_ip}"
                )
                logger.debug(f"[SecurityMiddleware] Method: {request.method}")
                logger.debug(f"[SecurityMiddleware] URL: {request.url}")
                logger.debug(f"[SecurityMiddleware] Headers: {dict(request.headers)}")

            # OPTIONS 요청은 항상 허용
            if request.method == "OPTIONS":
                response = Response(status_code=200)
                self._add_cors_headers(response, request.headers.get("origin"))
                return response

            # Debug mode에서는 로컬호스트 요청 허용
            if settings.DEBUG and client_ip in ["127.0.0.1", "localhost", "::1"]:
                response = await call_next(request)
                self._add_security_headers(response)
                self._add_cors_headers(response, request.headers.get("origin"))
                return response

            # 운영 환경에서만 보안 검사 수행
            if not settings.DEBUG:
                if self._is_ip_blocked(client_ip):
                    logger.warning(
                        f"[SecurityMiddleware] Blocked IP attempt: {client_ip}"
                    )
                    raise SecurityException(
                        detail="접근이 차단되었습니다", status_code=403
                    )

                if self._is_rate_limited(client_ip):
                    logger.warning(
                        f"[SecurityMiddleware] Rate limit exceeded for IP: {client_ip}"
                    )
                    self._block_ip(client_ip)
                    raise SecurityException(
                        detail="요청이 너무 빈번합니다",
                        status_code=429,
                        headers={"Retry-After": "60"},
                    )

            # 파일 크기 제한은 항상 적용
            content_length = request.headers.get("content-length")
            if content_length and int(content_length) > settings.MAX_REQUEST_SIZE:
                logger.warning(
                    f"[SecurityMiddleware] Request size exceeded from IP: {client_ip}"
                )
                raise SecurityException(detail="요청이 너무 큽니다", status_code=413)

            response = await call_next(request)

            # Debug mode에서는 보안 헤더 완화
            if settings.DEBUG:
                self._add_debug_security_headers(response)
            else:
                self._add_security_headers(response)

            self._add_cors_headers(response, request.headers.get("origin"))

            process_time = time.time() - start_time
            response.headers["X-Process-Time"] = str(process_time)

            if settings.DEBUG:
                logger.debug(
                    f"[SecurityMiddleware] Request processed in {process_time:.3f} seconds"
                )

            return response

        except Exception as e:
            logger.error(
                f"[SecurityMiddleware] Error processing request from {client_ip}: {str(e)}",
                exc_info=settings.DEBUG,
            )
            if isinstance(e, SecurityException):
                raise e
            raise SecurityException(
                detail=str(e) if settings.DEBUG else "보안 위반이 감지되었습니다",
                status_code=400,
            )

    def _get_client_ip(self, request: Request) -> str:
        """클라이언트 IP 주소를 안전하게 가져옵니다."""
        if request.client and request.client.host:
            return request.client.host
        return "unknown"

    def _is_ip_blocked(self, ip: str) -> bool:
        """IP 차단 여부 확인"""
        if ip in self._blocked_ips:
            if time.time() - self._blocked_ips[ip] > 3600:
                del self._blocked_ips[ip]
                logger.info("IP unblocked: %s", ip)
                return False
            return True
        return False

    def _block_ip(self, ip: str) -> None:
        """IP 차단"""
        self._blocked_ips[ip] = time.time()
        logger.warning("IP blocked: %s", ip)

    def _is_rate_limited(self, ip: str) -> bool:
        """요청 속도 제한 확인"""
        now = time.time()
        if ip not in self._ip_rate_limits:
            self._ip_rate_limits[ip] = []

        self._ip_rate_limits[ip] = [t for t in self._ip_rate_limits[ip] if now - t < 60]

        self._ip_rate_limits[ip].append(now)
        return len(self._ip_rate_limits[ip]) > settings.RATE_LIMIT_PER_MINUTE

    @staticmethod
    async def _check_malicious_patterns(patterns: List[str], request: Request) -> None:
        """악성 패턴 검사"""
        url = str(request.url)
        for pattern in patterns:
            if re.search(pattern, url):
                client_ip = request.client.host if request.client else "unknown"
                logger.warning("Malicious pattern detected from %s: %s", client_ip, url)
                raise SecurityException(detail="악성 패턴이 감지되었습니다")

        if request.method in ["POST", "PUT", "PATCH"]:
            body = await request.body()
            body_str = body.decode()
            for pattern in patterns:
                if re.search(pattern, body_str):
                    client_ip = request.client.host if request.client else "unknown"
                    logger.warning(
                        "Malicious pattern detected in body from %s", client_ip
                    )
                    raise SecurityException(detail="악성 패턴이 감지되었습니다")

    @staticmethod
    def _validate_security_headers(request: Request) -> None:
        """보안 헤더 검증"""
        origin = request.headers.get("origin")
        if origin:  # origin이 있을 때만 검사
            if origin not in settings.ALLOWED_ORIGINS and not settings.DEBUG:
                logger.warning(f"Unauthorized origin attempt: {origin}")
                raise SecurityException(detail="허용되지 않은 Origin입니다")

        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("content-type", "").lower()
            if not content_type:
                return  # content-type이 없는 경우는 허용

            # multipart/form-data도 허용
            if (
                "application/json" not in content_type
                and "multipart/form-data" not in content_type
            ):
                logger.warning(f"Invalid content-type: {content_type}")
                raise SecurityException(detail="지원하지 않는 Content-Type입니다")

    @staticmethod
    def _add_security_headers(response: Response) -> None:
        """보안 응답 헤더 추가"""
        headers = settings.SECURITY_HEADERS.copy()

        # 개발 환경에서는 일부 보안 헤더를 완화
        if settings.DEBUG:
            headers["Content-Security-Policy"] = (
                "default-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "img-src 'self' data: https:; "
                "style-src 'self' 'unsafe-inline'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'"
            )

        for header, value in headers.items():
            response.headers[header] = value

    def _add_debug_security_headers(self, response: Response) -> None:
        """Debug mode에서 사용할 완화된 보안 헤더"""
        headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "SAMEORIGIN",
            "Content-Security-Policy": (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: validator.swagger.io; "
                "font-src 'self' data:; "
                "connect-src 'self' validator.swagger.io; "
                "frame-src 'self';"
            ),
        }
        for header, value in headers.items():
            response.headers[header] = value

    def _add_cors_headers(
        self, response: Response, origin: Optional[str] = None
    ) -> None:
        """CORS 헤더를 추가합니다."""
        if settings.DEBUG:
            # Debug mode에서는 모든 CORS 헤더 허용
            response.headers["Access-Control-Allow-Origin"] = origin or "*"
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Methods"] = "*"
            response.headers["Access-Control-Allow-Headers"] = "*"
        elif origin and origin in settings.ALLOWED_ORIGINS:
            # 운영 환경에서는 허용된 origin만
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Methods"] = ", ".join(
                settings.ALLOWED_METHODS
            )
            response.headers["Access-Control-Allow-Headers"] = ", ".join(
                settings.ALLOWED_HEADERS
            )

        response.headers["Access-Control-Max-Age"] = "3600"


class MetricsMiddleware(BaseHTTPMiddleware):
    """메트릭스 수집 미들웨어"""

    @staticmethod
    async def dispatch(request: Request, call_next: Callable) -> FastAPIResponse:
        method = request.method
        path = request.url.path
        start_time = time.time()

        try:
            response = await call_next(request)

            REQUEST_LATENCY.labels(method=method, endpoint=path).observe(
                time.time() - start_time
            )

            REQUEST_COUNT.labels(
                method=method, endpoint=path, status=response.status_code
            ).inc()

            return response

        except Exception as e:
            API_ERROR_COUNT.labels(error_type=type(e).__name__).inc()
            raise


def metrics() -> FastAPIResponse:
    """Prometheus 메트릭 데이터를 반환합니다."""
    return FastAPIResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)
