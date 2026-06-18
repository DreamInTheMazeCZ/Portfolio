# 필요한 모듈들을 임포트합니다.
import logging.config
from functools import lru_cache  # 함수 결과를 캐시하기 위한 데코레이터
from typing import Any, Dict, List

from pydantic import ConfigDict, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    애플리케이션의 모든 설정을 관리하는 클래스입니다.
    환경 변수나 .env 파일에서 설정값을 자동으로 로드합니다.

    설정값 우선순위:
    1. 환경 변수
    2. .env 파일
    3. 기본값
    """

    # API 관련 설정
    API_V1_STR: str = "/api/v1"  # API 버전 접두사
    PROJECT_NAME: str = "WeSeed AI API"  # 프로젝트 이름
    PROJECT_DESCRIPTION: str = "WeSeed AI - Restful API Server"  # 프로젝트 설명
    VERSION: str = "1.0.0"  # 프로젝트 버전

    # OpenAI API 설정
    OPENAI_API_KEY: str  # OpenAI API 키 (필수값)
    OPENAI_MODEL: str = "gpt-4"  # 사용할 GPT 모델
    MAX_TOKENS: int = 4096  # 최대 토큰 수 (입력+출력 합계의 제한)
    TEMPERATURE: float = 0.7  # 응답의 창의성 수준 (0: 보수적, 1: 창의적)

    # 성능 관련 설정
    API_TIMEOUT: float = 30.0  # API 호출 제한 시간 (초)
    MAX_SESSIONS: int = 1000  # 동시에 유지할 수 있는 최대 세션 수
    MAX_HISTORY_PER_SESSION: int = 50  # 각 세션당 저장할 최대 대화 기록 수
    CLEANUP_INTERVAL: int = 3600  # 세션 정리 주기 (초)

    # 데이터베이스 연결 설정
    DB_POOL_SIZE: int = 20  # DB 연결 풀 크기
    DB_MAX_OVERFLOW: int = 10  # 풀 크기를 초과할 수 있는 최대 연결 수
    DB_POOL_TIMEOUT: int = 30  # DB 연결 대기 제한 시간 (초)

    # 다국어 지원 설정
    DEFAULT_LANGUAGE: str = "ko"  # 기본 언어 (한국어)
    RESOURCES_PATH: str = "resources"  # 언어 리소스 파일 경로

    # 환경 설정
    ENVIRONMENT: str = "development"  # 실행 환경 (development/production)
    DEBUG: bool = True  # 디버그 모드 활성화 여부

    # 로깅 설정
    LOG_LEVEL: str = "INFO"  # 로그 레벨 (DEBUG/INFO/WARNING/ERROR/CRITICAL)
    LOG_FORMAT: str = (
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"  # 로그 형식
    )
    LOG_FILE: str = "./logs/app.log"  # 로그 파일 경로

    # 보안 관련 설정
    API_KEY: str  # API 키 (필수값)
    JWT_SECRET_KEY: str  # JWT 토큰 암호화 키
    SESSION_SECRET_KEY: str  # 세션 암호화 키
    JWT_ALGORITHM: str = "HS256"  # JWT 암호화 알고리즘
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30  # 액세스 토큰 만료 시간(분)

    # 비밀번호 정책 설정
    PASSWORD_POLICY: Dict[str, Any] = {
        "min_length": 12,
        "require_uppercase": True,
        "require_lowercase": True,
        "require_numbers": True,
        "require_special_chars": True,
        "max_login_attempts": 5,
        "lockout_duration": 15,  # minutes
        "password_history": 5,  # 이전 비밀번호 재사용 금지 개수
        "expire_days": 90,  # 비밀번호 만료 일수
    }

    # CORS 설정
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost",
        "http://localhost:3000",
        "http://localhost:5000",
        "http://localhost:8000",
        "http://localhost:8080",
        "http://127.0.0.1",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5000",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:8080",
    ]
    ALLOWED_METHODS: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    ALLOWED_HEADERS: List[str] = (
        ["*"] if DEBUG else ["Authorization", "Content-Type", "X-API-Key"]
    )

    # 보안 제한 설정
    MAX_REQUEST_SIZE: int = 1024 * 1024  # 최대 요청 크기 (1MB)
    RATE_LIMIT_PER_MINUTE: int = 60  # 분당 최대 요청 수
    MAX_CONTENT_LENGTH: int = 4096  # 최대 컨텐츠 길이
    PASSWORD_MIN_LENGTH: int = 12  # 최소 비밀번호 길이

    # SSL/TLS 설정 보강
    SSL_CERTIFICATE: str = ""  # SSL 인증서 경로
    SSL_KEY: str = ""  # SSL 키 경로
    SSL_OPTIONS: Dict[str, Any] = {
        "minimum_version": "TLSv1.2",
        "cipher_suite": "ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256",
        "prefer_server_ciphers": True,
        "session_tickets": False,
    }
    FORCE_SSL: bool = True  # HTTPS 강제 여부

    # 세션 보안 설정
    SESSION_COOKIE_SECURE: bool = True  # HTTPS에서만 쿠키 전송
    SESSION_COOKIE_HTTPONLY: bool = True  # JavaScript에서 쿠키 접근 불가
    SESSION_COOKIE_SAMESITE: str = "Lax"  # CSRF 방지
    SESSION_EXPIRE_MINUTES: int = 60  # 세션 만료 시간(분)

    # 보안 헤더 설정 강화
    SECURITY_HEADERS: Dict[str, str] = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
        "Content-Security-Policy": (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: validator.swagger.io; "
            "font-src 'self' data:; "
            "connect-src 'self' validator.swagger.io; "
            "frame-src 'self';"
        ),
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
        "X-Permitted-Cross-Domain-Policies": "none",
        "Cross-Origin-Embedder-Policy": "unsafe-none",
        "Cross-Origin-Opener-Policy": "same-origin",
        "Cross-Origin-Resource-Policy": "cross-origin",
    }

    # 입력 검증 설정
    INPUT_VALIDATION: Dict[str, Any] = {
        "max_question_length": 4000,
        "allowed_characters": "가-힣a-zA-Z0-9 .,!?()-_",
        "blocked_patterns": [
            r"<script>",
            r"javascript:",
            r"onload=",
            r"onerror=",
            r"SELECT.*FROM",
            r"INSERT.*INTO",
            r"UPDATE.*SET",
            r"DELETE.*FROM",
            r"DROP.*TABLE",
            r"UNION.*SELECT",
        ],
    }

    # 타임아웃 및 제한 설정값 검증
    @field_validator("API_TIMEOUT", "DB_POOL_TIMEOUT", "SESSION_EXPIRE_MINUTES")
    @classmethod
    def validate_timeout_values(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("타임아웃 값은 0보다 커야 합니다")
        if v > 300:  # 5분 제한
            raise ValueError("타임아웃 값이 너무 큽니다 (최대 300초)")
        return v

    @field_validator("MAX_TOKENS", "MAX_CONTENT_LENGTH", "MAX_REQUEST_SIZE")
    @classmethod
    def validate_size_limits(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("크기 제한은 0보다 커야 합니다")
        return v

    @field_validator("DB_POOL_SIZE", "DB_MAX_OVERFLOW")
    @classmethod
    def validate_db_pool_settings(cls, v: int) -> int:
        if v < 0:
            raise ValueError("DB 풀 설정은 음수가 될 수 없습니다")
        if v > 100:  # 과도한 DB 연결 방지
            raise ValueError("DB 풀 설정이 너무 큽니다 (최대 100)")
        return v

    @field_validator("TEMPERATURE")
    @classmethod
    def validate_temperature(cls, v: float) -> float:
        if not 0 <= v <= 1:
            raise ValueError("Temperature 값은 0과 1 사이여야 합니다")
        return v

    @property
    def logging_config(self) -> Dict[str, Any]:
        """
        로깅 설정을 반환합니다.

        이 설정은 다음을 포함합니다:
        - 콘솔 출력
        - 파일 출력 (자동 로테이션)
        - 로그 형식 지정
        - 로그 레벨 설정

        Returns:
            Dict[str, Any]: 로깅 설정 딕셔너리
        """
        return {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {"default": {"format": self.LOG_FORMAT}},
            "handlers": {
                # 콘솔 출력 핸들러
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "default",
                    "level": self.LOG_LEVEL,
                },
                # 파일 출력 핸들러 (자동 로테이션)
                "file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "formatter": "default",
                    "filename": self.LOG_FILE,
                    "maxBytes": 10485760,  # 10MB
                    "backupCount": 5,  # 최대 5개의 백업 파일 유지
                    "level": self.LOG_LEVEL,
                },
            },
            "loggers": {
                # 루트 로거 설정
                "": {"handlers": ["console", "file"], "level": self.LOG_LEVEL}
            },
        }

    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=True,
        secrets=["API_KEY", "JWT_SECRET_KEY", "OPENAI_API_KEY"],
    )


@lru_cache()
def get_settings() -> Settings:
    """
    설정 객체를 생성하고 캐시합니다.
    """
    settings = Settings()
    logging.config.dictConfig(settings.logging_config)
    return settings
