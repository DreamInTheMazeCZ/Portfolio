# 보안 관련 모듈 추가
import logging
import secrets
import time
from typing import Any, Dict, List, Union

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader

from core.exceptions import AIServiceException
from core.i18n import get_i18n
from core.session import session_manager
from core.settings import get_settings
from core.utils import sanitize_input, validate_session_id
from model.schemas import AIResponse, Question
from service.services import create_ai_response, get_available_models
from service.agent import ask_return

# API 키 헤더 설정
API_KEY_HEADER = APIKeyHeader(name="X-API-Key")

logger = logging.getLogger(__name__)
settings = get_settings()
i18n = get_i18n()


# 레이트 리미팅을 위한 딕셔너리
request_counts = {}
RATE_LIMIT_WINDOW = 3600  # 1시간
MAX_REQUESTS = 100  # 시간당 최대 요청 수
MAX_TRACKED_IPS = 10000  # 최대 추적 IP 수


async def clean_request_counts():
    """주기적으로 request_counts를 정리합니다."""
    global request_counts
    current_time = time.time()

    # 만료된 항목 제거
    request_counts = {
        ip: (count, timestamp)
        for ip, (count, timestamp) in request_counts.items()
        if current_time - timestamp < RATE_LIMIT_WINDOW
    }

    # 크기 제한 적용
    if len(request_counts) > MAX_TRACKED_IPS:
        # 가장 오래된 항목부터 제거
        sorted_items = sorted(request_counts.items(), key=lambda x: x[1][1])
        request_counts = dict(sorted_items[:MAX_TRACKED_IPS])


router = APIRouter(
    prefix=f"{settings.API_V1_STR}/chat",
    tags=["chat"],
    responses={
        400: {"description": "잘못된 요청"},
        401: {"description": "인증되지 않은 요청"},
        403: {"description": "권한 없음"},
        404: {"description": "리소스를 찾을 수 없음"},
        429: {"description": "요청 한도 초과"},
        500: {"description": "서버 내부 오류"},
        503: {"description": "서비스 이용 불가"},
    },
)


async def verify_api_key(request: Request) -> str:
    """API 키를 검증하고 레이트 리미팅을 적용"""
    await clean_request_counts()

    # IP 기반 브루트포스 공격 방지
    client_ip = request.client.host if request.client else "unknown"
    current_time = time.time()

    # 동일 IP의 연속 실패 횟수 확인
    failed_attempts = request.app.state.failed_auth.get(
        client_ip, {"count": 0, "first_attempt": current_time}
    )

    # 15분 이상 지났으면 실패 횟수 초기화
    if current_time - failed_attempts["first_attempt"] > 900:  # 15분
        failed_attempts = {"count": 0, "first_attempt": current_time}

    # 실패 횟수가 10회 이상이면 일시적 차단
    if failed_attempts["count"] >= 10:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="너무 많은 인증 시도가 있었습니다. 잠시 후 다시 시도해주세요.",
            headers={"Retry-After": "900"},
        )

    api_key = request.headers.get("X-API-Key")
    if not api_key:
        failed_attempts["count"] += 1
        request.app.state.failed_auth[client_ip] = failed_attempts
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="API 키가 필요합니다"
        )

    if not secrets.compare_digest(api_key, settings.API_KEY):  # 타이밍 공격 방지
        failed_attempts["count"] += 1
        request.app.state.failed_auth[client_ip] = failed_attempts
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="잘못된 API 키입니다"
        )

    # 레이트 리미팅 적용
    if client_ip in request_counts:
        count, timestamp = request_counts[client_ip]
        if count >= MAX_REQUESTS:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="요청 한도를 초과했습니다",
                headers={"Retry-After": str(RATE_LIMIT_WINDOW)},
            )
        request_counts[client_ip] = (count + 1, current_time)
    else:
        request_counts[client_ip] = (1, current_time)

    # 성공 시 실패 횟수 초기화
    if client_ip in request.app.state.failed_auth:
        del request.app.state.failed_auth[client_ip]

    return api_key


@router.get("/docs", include_in_schema=False)
async def get_custom_swagger_ui() -> Any:
    """API 문서를 제공하는 Swagger UI 엔드포인트입니다."""
    return {"message": "API 문서는 메인 애플리케이션의 /docs 에서 확인할 수 있습니다."}


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    response_model_exclude_none=True,
    summary="API 소개",
    description="AI Q&A API의 사용 방법을 안내합니다.",
)
async def get_api_info() -> Dict[str, Any]:
    """API 소개 정보를 반환합니다."""
    return {
        "message": i18n.get("common.welcome"),
        "사용 예시": {
            "endpoint": f"{settings.API_V1_STR}/chat/ask",
            "method": "POST",
            "request_body": {
                "text": "파이썬으로 'Hello, World!'를 출력하는 방법을 알려주세요."
            },
        },
    }


@router.post("/ask")
async def create_question(
    question: Question,
    response: Response,
    request: Request,
    api_key: str = Depends(verify_api_key),
) -> AIResponse:
    """사용자의 질문을 처리하고 AI 응답을 생성"""
    try:
        # 개발 환경에서는 CSRF 검증 건너뛰기
        if not settings.DEBUG:
            if request.headers.get("X-CSRF-Token") != request.cookies.get("csrf_token"):
                logger.warning("CSRF token validation failed")
                raise HTTPException(
                    status_code=403, detail="CSRF 토큰이 유효하지 않습니다"
                )

        # Content-Type 검증 - application/json 또는 multipart/form-data 허용
        content_type = request.headers.get("content-type", "").lower()
        if not (
            "application/json" in content_type or "multipart/form-data" in content_type
        ):
            logger.warning(f"Invalid content-type: {content_type}")
            raise HTTPException(
                status_code=415, detail="지원하지 않는 Content-Type입니다"
            )

        # 세션 ID 검증 - 없으면 새로 생성
        session_id = request.cookies.get("session_id")
        if not session_id or not validate_session_id(session_id):
            session_id = session_manager.create_session()
            logger.info(f"Created new session: {session_id}")

        start_time = time.time()

        # 입력값 검증
        try:
            sanitized_text = sanitize_input(question.text)
        except ValueError as e:
            logger.warning(f"Input validation failed: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))

        ai_response = await create_ai_response(sanitized_text, session_id)

        # 응답 헤더 보안 설정
        process_time = time.time() - start_time
        response.headers.update(settings.SECURITY_HEADERS)
        response.headers["X-Process-Time"] = str(process_time)

        # 세션 ID를 쿠키로 설정
        response.set_cookie(
            key="session_id",
            value=session_id,
            max_age=settings.SESSION_EXPIRE_MINUTES * 60,
            httponly=True,
            secure=settings.FORCE_SSL,
            samesite="lax",
        )

        if not ai_response.success:
            logger.error(f"AI service error: {ai_response.error}")
            raise AIServiceException(detail=ai_response.error)

        return ai_response

    except Exception as e:
        logger.error(f"Service error in create_question: {str(e)}", exc_info=True)
        if isinstance(e, (HTTPException, AIServiceException)):
            raise
        raise HTTPException(
            status_code=500, detail=i18n.get("errors.internal_server_error")
        )

# ===== 추가부분 =====
@router.post("/ask/agent")
async def create_question(
    question: Question,
) -> AIResponse:
    """사용자의 질문을 처리하고 AI 응답을 생성"""
    try:
        return ask_return(question.text)

    except Exception as e:
        logger.error(f"Service error in create_question: {str(e)}", exc_info=True)
        if isinstance(e, (HTTPException, AIServiceException)):
            raise
        raise HTTPException(
            status_code=500, detail=i18n.get("errors.internal_server_error")
        )


@router.get(
    "/conversation/{session_id}",
    status_code=status.HTTP_200_OK,
    response_model=Union[
        Dict[str, list], Dict[str, str]
    ],  # Allow both success and error responses
    summary=i18n.get("api.chat.conversation.summary"),
    description=i18n.get("api.chat.conversation.description"),
)
async def get_conversation_history(
    session_id: str, api_key: str = Depends(verify_api_key)
) -> Union[Dict[str, list], JSONResponse]:
    """대화 기록을 조회합니다."""
    try:
        # 세션 ID 검증
        if not validate_session_id(session_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="유효하지 않은 세션 ID입니다",
            )

        conversation = session_manager.get_session(
            session_id
        )  # Changed from get_conversation to get_session
        return {"conversation": conversation}
    except Exception as e:
        logger.error(
            i18n.get("logs.service_error", session_id=session_id, error=str(e))
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": i18n.get("errors.conversation_fetch_error")},
        )


@router.get(
    "/models",
    status_code=status.HTTP_200_OK,
    response_model=Union[
        Dict[str, list], Dict[str, str]
    ],  # Allow both success and error responses
    summary=i18n.get("api.chat.models.summary"),
    description=i18n.get("api.chat.models.description"),
)
async def get_models(
    api_key: str = Depends(verify_api_key),
) -> Union[Dict[str, list], JSONResponse]:
    try:
        model_list = await get_available_models()
        return {"models": model_list}
    except Exception as e:
        logger.error(i18n.get("logs.models_error", error=str(e)))
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"error": i18n.get("errors.models_fetch_error")},
        )


@router.delete(
    "/conversation/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary=i18n.get("api.chat.conversation.clear.summary"),
    description=i18n.get("api.chat.conversation.clear.description"),
)
async def delete_conversation(session_id: str, api_key: str = Depends(verify_api_key)):
    try:
        session_manager.clear_session(session_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except Exception as e:
        logger.error(
            i18n.get("logs.service_error", session_id=session_id, error=str(e))
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": i18n.get("errors.conversation_clear_error")},
        )
