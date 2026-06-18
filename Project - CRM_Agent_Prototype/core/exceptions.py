from typing import Any, Optional
from fastapi import HTTPException, status
from core.i18n import get_i18n
from core.utils import sanitize_log_content
import logging

logger = logging.getLogger(__name__)
i18n = get_i18n()

class BaseSecurityException(HTTPException):
    """보안 관련 기본 예외 클래스"""
    def __init__(
        self,
        detail: Any = None,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        headers: Optional[dict] = None,
        log_level: str = "warning"
    ) -> None:
        # 민감한 정보가 포함되지 않도록 상세 메시지 처리
        safe_detail = sanitize_log_content(str(detail)) if detail else None
        super().__init__(status_code=status_code, detail=safe_detail)
        
        # 보안 헤더 추가
        self.headers = headers or {}
        
        # 보안 이벤트 로깅
        log_func = getattr(logger, log_level)
        log_func(
            "Security event: %s, Status: %d, Detail: %s",
            self.__class__.__name__,
            status_code,
            safe_detail
        )

class AuthenticationException(BaseSecurityException):
    """인증 관련 예외"""
    def __init__(
        self,
        detail: Any = None,
        headers: Optional[dict] = None
    ) -> None:
        detail = detail or i18n.get("errors.authentication_failed")
        super().__init__(
            detail=detail,
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers=headers or {"WWW-Authenticate": "Bearer"},
            log_level="warning"
        )

class AuthorizationException(BaseSecurityException):
    """권한 관련 예외"""
    def __init__(
        self,
        detail: Any = None,
        headers: Optional[dict] = None
    ) -> None:
        detail = detail or i18n.get("errors.unauthorized")
        super().__init__(
            detail=detail,
            status_code=status.HTTP_403_FORBIDDEN,
            headers=headers,
            log_level="warning"
        )

class RateLimitException(BaseSecurityException):
    """레이트 리미팅 예외"""
    def __init__(
        self,
        detail: Any = None,
        retry_after: int = 3600
    ) -> None:
        detail = detail or i18n.get("errors.rate_limit_exceeded")
        super().__init__(
            detail=detail,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            headers={"Retry-After": str(retry_after)},
            log_level="warning"
        )

class ValidationException(BaseSecurityException):
    """입력값 검증 예외"""
    def __init__(
        self,
        detail: Any = None
    ) -> None:
        detail = detail or i18n.get("errors.validation_failed")
        super().__init__(
            detail=detail,
            status_code=status.HTTP_400_BAD_REQUEST,
            log_level="warning"
        )

class SecurityException(BaseSecurityException):
    """일반 보안 예외"""
    def __init__(
        self,
        detail: Any = None,
        status_code: int = status.HTTP_400_BAD_REQUEST
    ) -> None:
        detail = detail or i18n.get("errors.security_violation")
        super().__init__(
            detail=detail,
            status_code=status_code,
            log_level="error"
        )

class AIServiceException(BaseSecurityException):
    def __init__(
        self,
        detail: Any = None,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
    ) -> None:
        detail = detail or i18n.get("errors.server_error")
        super().__init__(
            detail=detail,
            status_code=status_code,
            log_level="error"
        )

class EmptyQuestionException(ValidationException):
    def __init__(
        self,
        detail: Any = None
    ) -> None:
        detail = detail or i18n.get("errors.empty_question")
        super().__init__(detail=detail)

class OpenAIAPIException(AIServiceException):
    def __init__(
        self,
        detail: Any = None,
        status_code: int = status.HTTP_503_SERVICE_UNAVAILABLE,
    ) -> None:
        detail = detail or i18n.get("errors.api_error")
        super().__init__(detail=detail, status_code=status_code)