import json
import logging
import re
from contextlib import contextmanager
from datetime import datetime
from typing import Dict, List, Literal, Sequence, TypedDict, Union

from openai import AsyncOpenAI, OpenAIError
from openai.types.chat import ChatCompletion
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam

from core.cache import response_cache
from core.exceptions import EmptyQuestionException, OpenAIAPIException
from core.i18n import get_i18n
from core.session import session_manager
from core.settings import get_settings
from core.utils import calculate_token_metrics as base_calculate_metrics
from core.utils import count_tokens
from model.schemas import AIResponse

# Initialize logging and settings
logger = logging.getLogger(__name__)
settings = get_settings()
i18n = get_i18n()

# Initialize OpenAI API v1.0.0+ async client
client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


class Message(TypedDict):
    role: str
    content: str
    timestamp: str


class ChatMessage(TypedDict):
    role: Literal["system", "user", "assistant"]
    content: str


@contextmanager
def manage_session_transaction(session_id: str):
    """세션 상태 변경을 안전하게 관리하는 컨텍스트 매니저입니다."""
    session_state: Sequence[Message] = session_manager.get_session(session_id)
    try:
        yield session_state
    except Exception as e:
        if session_state:
            session_manager.clear_session(session_id)
            for msg in session_state:
                role = msg.get("role")
                content = msg.get("content")
                if role in ("system", "user", "assistant") and content:
                    session_manager.add_message(
                        session_id=session_id, role=role, content=str(content)
                    )
        logger.error(
            i18n.get("logs.transaction_failed", session_id=session_id, error=str(e))
        )
        raise


def validate_openai_response(response: ChatCompletion) -> bool:
    """OpenAI API v1.0.0+ 응답의 유효성을 검증합니다."""
    try:
        # Basic response validation
        if (
            not response
            or not isinstance(response, ChatCompletion)
            or not response.choices
        ):
            return False

        choice = response.choices[0]
        content = choice.message.content if choice.message else None

        # Content validation
        return bool(content and content.strip())

    except (AttributeError, TypeError, ValueError):
        return False


def prepare_chat_completion_messages(
    conversation: Sequence[Dict[str, str]], question: str
) -> List[ChatMessage]:
    """채팅 메시지 목록을 준비합니다."""
    # System message with proper typing
    messages: List[ChatMessage] = [
        ChatMessage(
            role="system",
            content="You are now senior software engineer and always answer with korean",
        )
    ]

    # Add conversation history with validated roles
    if conversation:
        for msg in conversation[-settings.MAX_HISTORY_PER_SESSION :]:
            role = msg.get("role")
            content = msg.get("content")
            if role in ("system", "user", "assistant") and content:
                messages.append(ChatMessage(role=role, content=str(content)))

    # Add current question
    messages.append(ChatMessage(role="user", content=str(question)))

    # Token management
    total_tokens = count_tokens(
        [{"role": m["role"], "content": m["content"]} for m in messages]
    )
    max_allowed_tokens = 8192 - settings.MAX_TOKENS

    while total_tokens > max_allowed_tokens and len(messages) > 2:
        messages.pop(1)
        total_tokens = count_tokens(
            [{"role": m["role"], "content": m["content"]} for m in messages]
        )

    return messages


def sanitize_log_content(content: str, max_length: int = 100) -> str:
    """로그에 기록될 내용을 안전하게 처리합니다."""
    if not content:
        return ""
    # 민감한 정보 패턴
    patterns = [
        (r'api[-_]key["\']?\s*[:=]\s*["\']?[\w\-]+["\']?', "[API_KEY_MASKED]"),
        (r'password["\']?\s*[:=]\s*["\']?[\w\-]+["\']?', "[PASSWORD_MASKED]"),
        (r'token["\']?\s*[:=]\s*["\']?[\w\-]+["\']?', "[TOKEN_MASKED]"),
        (r'secret["\']?\s*[:=]\s*["\']?[\w\-]+["\']?', "[SECRET_MASKED]"),
    ]

    result = content
    for pattern, mask in patterns:
        result = re.sub(pattern, mask, result, flags=re.IGNORECASE)

    # 긴 내용 축약
    if len(result) > max_length:
        return result[:max_length] + "..."
    return result


async def create_ai_response(question: str, session_id: str) -> AIResponse:
    """사용자의 질문에 대한 AI 응답을 생성합니다."""
    start_time = datetime.now()

    try:
        # 1. 입력값 검증 및 로깅
        sanitized_question = sanitize_log_content(question)
        logger.info(
            i18n.get(
                "logs.question_received",
                session_id=session_id,
                question=sanitized_question,
            )
        )

        if not question.strip():
            logger.warning(i18n.get("logs.empty_question", session_id=session_id))
            raise EmptyQuestionException()

        # 2. 캐시된 응답 확인
        cached_response = response_cache.get(question)
        if (
            cached_response
            and isinstance(cached_response, dict)
            and "response" in cached_response
            and isinstance(cached_response["response"], str)
        ):
            logger.info(i18n.get("logs.cache_hit", session_id=session_id))
            process_time = (datetime.now() - start_time).total_seconds()

            with manage_session_transaction(session_id):
                session_manager.add_message(session_id, "user", question)
                session_manager.add_message(
                    session_id, "assistant", cached_response["response"]
                )

            cached_metrics = cached_response.get("metrics", {})
            if not isinstance(cached_metrics, dict):
                cached_metrics = {}

            return AIResponse(
                question=question,
                response=cached_response["response"],
                success=True,
                process_time=process_time,
                timestamp=datetime.now(),
                metrics={
                    "cached": True,
                    "original_metrics": cached_metrics,
                    "tokens_question": cached_metrics.get("tokens_question", 0),
                    "tokens_response": cached_metrics.get("tokens_response", 0),
                    "total_tokens": cached_metrics.get("total_tokens", 0),
                },
            )

        # 3. OpenAI API 호출 준비 및 실행
        with manage_session_transaction(session_id) as session_state:
            conversation = session_state
            messages = prepare_chat_completion_messages(conversation, question)

            try:
                completion = await _call_openai_with_retry(messages)

                if not validate_openai_response(completion):
                    raise OpenAIAPIException(detail=i18n.get("errors.invalid_response"))

                response_content = completion.choices[0].message.content
                if not response_content:
                    raise OpenAIAPIException(detail=i18n.get("errors.empty_response"))

                # 4. 응답 처리 및 메트릭스 계산
                usage = completion.usage if completion.usage else None
                metrics = {
                    "tokens_used": usage.total_tokens if usage else 0,
                    "prompt_tokens": usage.prompt_tokens if usage else 0,
                    "completion_tokens": usage.completion_tokens if usage else 0,
                    "tokens_question": usage.prompt_tokens if usage else 0,
                    "tokens_response": usage.completion_tokens if usage else 0,
                    "total_tokens": usage.total_tokens if usage else 0,
                    "api_latency": float((datetime.now() - start_time).total_seconds()),
                    "cached": False,
                    "content": response_content,
                }

                # 5. 응답 캐싱
                cache_data = {
                    "response": response_content,
                    "metrics": metrics,
                }
                try:
                    response_cache.set(question, cache_data)
                except Exception as cache_error:
                    logger.error(f"Cache storage error: {str(cache_error)}")

                # 6. 세션 업데이트
                session_manager.add_message(session_id, "user", question)
                session_manager.add_message(session_id, "assistant", response_content)

                # 7. 응답 생성
                process_time = (datetime.now() - start_time).total_seconds()
                safe_metrics = {
                    k: v
                    for k, v in metrics.items()
                    if k not in ["content", "full_response"]
                }

                logger.info(
                    i18n.get(
                        "logs.success",
                        session_id=session_id,
                        time=process_time,
                        metrics=json.dumps(safe_metrics),
                    )
                )

                return AIResponse(
                    question=question,
                    response=response_content,
                    success=True,
                    process_time=process_time,
                    timestamp=datetime.now(),
                    metrics=metrics,
                )

            except OpenAIError as api_error:
                logger.error(
                    i18n.get(
                        "logs.api_error",
                        session_id=session_id,
                        error=sanitize_log_content(str(api_error)),
                    )
                )
                raise OpenAIAPIException(
                    detail=i18n.get("errors.api_error", error=str(api_error))
                )

    except Exception as e:
        logger.error(
            i18n.get(
                "logs.service_error",
                session_id=session_id,
                error=sanitize_log_content(str(e)),
            )
        )
        process_time = (datetime.now() - start_time).total_seconds()
        error_metrics = {
            "error": True,
            "error_type": type(e).__name__,
            "tokens_used": 0,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "tokens_question": 0,
            "tokens_response": 0,
            "total_tokens": 0,
            "api_latency": process_time,
        }
        return AIResponse(
            question=question,
            error=str(e),
            success=False,
            process_time=process_time,
            timestamp=datetime.now(),
            metrics=error_metrics,
        )


async def _call_openai_with_retry(
    messages: List[ChatMessage], max_retries: int = 3
) -> ChatCompletion:
    """OpenAI API 호출을 재시도 로직과 함께 처리합니다."""
    from asyncio import TimeoutError, sleep
    from random import random

    last_error = None

    for attempt in range(max_retries):
        try:
            # OpenAI API v1.0.0+ 메시지 검증
            validated_messages = []
            for msg in messages:
                role = msg.get("role")
                content = msg.get("content")
                if role in ("system", "user", "assistant") and isinstance(content, str):
                    validated_messages.append({"role": role, "content": content})

            if not validated_messages:
                raise OpenAIError("유효한 메시지가 없습니다")

            completion = await client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=validated_messages,
                max_tokens=settings.MAX_TOKENS,
                n=1,
                temperature=settings.TEMPERATURE,
            )
            return completion

        except TimeoutError:
            logger.warning(i18n.get("logs.api_timeout", attempt=attempt + 1))
            last_error = TimeoutError("API 응답 시간 초과")

        except OpenAIError as e:
            last_error = e
            logger.warning(
                i18n.get("logs.api_retry", attempt=attempt + 1, error=str(e))
            )

        if attempt < max_retries - 1:
            backoff_time = (2**attempt) + (random() * 0.1)
            await sleep(backoff_time)
            continue

    raise last_error or OpenAIError("알 수 없는 API 오류가 발생했습니다")


async def get_available_models() -> List[str]:
    """
    사용 가능한 OpenAI 모델 목록을 조회합니다.

    Returns:
        List[str]: 사용 가능한 모델 ID 목록

    Raises:
        OpenAIAPIException: API 호출 중 오류 발생 시
    """
    try:
        logger.info(i18n.get("logs.models_fetch"))
        models_response = await client.models.list()
        model_list = [str(model.id) for model in models_response.data]
        logger.info(i18n.get("logs.models_success", count=len(model_list)))
        return model_list
    except Exception as e:
        logger.error(i18n.get("logs.models_error", error=str(e)))
        raise OpenAIAPIException(detail=i18n.get("errors.models_fetch_error"))


def calculate_token_metrics(
    question: str, response: str | None
) -> Dict[str, Union[int, float, str]]:
    """토큰 수를 계산하고 메트릭을 생성합니다."""
    if response is None:
        response = ""

    base_metrics = base_calculate_metrics(prompt=question, response=response)
    metrics: Dict[str, Union[int, float, str]] = {
        "tokens_used": base_metrics["total_tokens"],
        "prompt_tokens": base_metrics["prompt_tokens"],
        "completion_tokens": base_metrics["completion_tokens"],
        "tokens_question": base_metrics["prompt_tokens"],  # For backward compatibility
        "tokens_response": base_metrics[
            "completion_tokens"
        ],  # For backward compatibility
        "total_tokens": base_metrics["total_tokens"],  # For backward compatibility
        "api_latency": 0.0,  # Will be set later in create_ai_response
        "content": response,
    }
    return metrics
