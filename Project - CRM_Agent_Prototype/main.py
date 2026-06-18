# FastAPI와 필요한 모듈들을 임포트합니다.
import os
import sys
from datetime import datetime

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer
from starlette.middleware.sessions import SessionMiddleware

from api.chat import router as chat_router
from core.middleware import MetricsMiddleware, SecurityMiddleware, metrics
from core.settings import get_settings
from core.utils import secure_random_string

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 환경 설정을 가져옵니다.
settings = get_settings()

def create_application() -> FastAPI:
    """
    FastAPI 애플리케이션을 생성하고 설정하는 함수입니다.
    
    Returns:
        FastAPI: 설정이 완료된 FastAPI 애플리케이션 인스턴스
    """
    # FastAPI 인스턴스를 생성하고 기본 설정을 합니다.
    application = FastAPI(
        title=settings.PROJECT_NAME,
        description=settings.PROJECT_DESCRIPTION,
        version=settings.VERSION,
        docs_url="/docs",  # Always enable Swagger UI
        redoc_url="/redoc",  # Always enable ReDoc
        openapi_url="/openapi.json",  # Always expose OpenAPI schema
        swagger_ui_parameters={"persistAuthorization": True},
        openapi_tags=[
            {
                "name": "chat",
                "description": "대화형 AI 응답 관련 API 엔드포인트",
                "externalDocs": {
                    "description": "OpenAI API 문서",
                    "url": "https://platform.openai.com/docs/api-reference/chat"
                }
            },
            {
                "name": "monitoring",
                "description": "시스템 모니터링 관련 API 엔드포인트"
            }
        ]
    )

    # 실패한 인증 시도를 추적하기 위한 상태 초기화
    application.state.failed_auth = {}

    # CORS 미들웨어를 먼저 적용하여 preflight 요청 처리
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=settings.ALLOWED_METHODS,
        allow_headers=settings.ALLOWED_HEADERS,
        expose_headers=["X-Process-Time", "X-API-Key"],
        max_age=3600,  # 프리플라이트 요청 캐시 시간
    )

    # TrustedHostMiddleware를 다음으로 적용
    application.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["localhost", "127.0.0.1", "localhost:8000", "127.0.0.1:8000"]
    )

    # SecurityMiddleware를 세션 미들웨어 전에 적용
    application.add_middleware(SecurityMiddleware)

    # 세션 미들웨어 설정
    application.add_middleware(
        SessionMiddleware,
        secret_key=settings.SESSION_SECRET_KEY,
        session_cookie="session",
        max_age=settings.SESSION_EXPIRE_MINUTES * 60,
        same_site="lax",
        https_only=settings.FORCE_SSL
    )
    
    # 메트릭 미들웨어 추가
    application.add_middleware(MetricsMiddleware)

    # 보안 헤더 적용
    @application.middleware("http")
    async def add_security_headers(request: Request, call_next):
        response = await call_next(request)
        # 운영 환경에서는 모든 보안 헤더 적용
        if not settings.DEBUG:
            for header, value in settings.SECURITY_HEADERS.items():
                response.headers[header] = value
        return response

    # 글로벌 에러 핸들러 추가
    @application.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.detail,
                "path": request.url.path,
                "method": request.method,
                "timestamp": datetime.now().isoformat()
            }
        )

    # API 라우터 등록
    application.include_router(chat_router)

    return application

# FastAPI 애플리케이션 인스턴스를 생성합니다.
app = create_application()

# 직접 실행될 때의 설정
if __name__ == "__main__":
    # SSL/TLS 설정
    ssl_config = {}
    if settings.SSL_CERTIFICATE and settings.SSL_KEY:
        ssl_config.update({
            'ssl_keyfile': settings.SSL_KEY,
            'ssl_certfile': settings.SSL_CERTIFICATE,
            'ssl_version': settings.SSL_OPTIONS["minimum_version"],
            'ssl_ciphers': settings.SSL_OPTIONS["cipher_suite"]
        })

    # uvicorn 서버를 시작합니다.
    uvicorn.run(
        "main:app",
        host="0.0.0.0",  # Allow external connections
        port=8000,
        # reload=settings.DEBUG,  # 개발 환경에서만 자동 재시작
        log_level="debug" if settings.DEBUG else "info",
        **ssl_config,
        proxy_headers=True,  # 프록시 헤더 처리
        forwarded_allow_ips="*",  # Allow all forwarded IPs in debug mode
        server_header=False,  # Server 헤더 숨김
        date_header=False  # Date 헤더 숨김
    )