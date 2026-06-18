import time
from typing import Any
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from openai.types.chat import ChatCompletion, ChatCompletionMessage
from openai.types.chat.chat_completion import Choice

from api.chat import request_counts
from core.cache import response_cache
from core.exceptions import AIServiceException
from core.session import session_manager
from core.settings import get_settings
from main import app

settings = get_settings()
client = TestClient(app)


@pytest.fixture
def mock_openai_response() -> ChatCompletion:
    message = ChatCompletionMessage(content="테스트 응답입니다.", role="assistant")
    return ChatCompletion(
        id="chatcmpl-test",
        choices=[Choice(message=message, index=0, finish_reason="stop", logprobs=None)],
        created=int(time.time()),
        model="gpt-3.5-turbo",
        object="chat.completion",
        system_fingerprint=None,
    )


def test_root_endpoint() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()


@patch("openai.resources.chat.completions.Completions.create")
def test_ask_question(mock_openai: Any, mock_openai_response: ChatCompletion) -> None:
    mock_openai.return_value = mock_openai_response

    response = client.post("/api/v1/chat/ask", json={"text": "테스트 질문입니다."})

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "response" in data
    assert data["question"] == "테스트 질문입니다."
    assert mock_openai.call_count == 1


def test_rate_limiting() -> None:
    """레이트 리미팅 테스트"""
    settings = get_settings()

    # API 키 없이 요청하여 인증 실패 확인
    response = client.post("/api/v1/chat/ask", json={"text": "테스트"})
    assert response.status_code == 401

    # 레이트 리밋 초과 테스트
    headers = {"X-API-Key": settings.API_KEY}
    
    # First request should succeed
    response = client.post("/api/v1/chat/ask", json={"text": "테스트"}, headers=headers)
    assert response.status_code == 200

    # Manually set the request count to exceed limit
    client_ip = "testclient"
    request_counts[client_ip] = (settings.RATE_LIMIT_PER_MINUTE + 1, time.time())

    # Next request should fail with 429
    response = client.post("/api/v1/chat/ask", json={"text": "테스트"}, headers=headers)
    assert response.status_code == 429
    assert "error" in response.json()


def test_input_validation() -> None:
    """입력값 검증 테스트"""
    headers = {"X-API-Key": get_settings().API_KEY}

    test_cases = [
        ("<script>alert('xss')</script>", "XSS 공격 시도", 400),
        ("SELECT * FROM users", "SQL 인젝션 시도", 400),
        ("DROP TABLE users", "SQL 인젝션 시도", 400),
        ("", "빈 입력", 422),  # Pydantic validation
        ("   ", "공백 입력", 400),  # Custom validation
        ("a" * 4001, "최대 길이 초과", 422),  # Pydantic validation
    ]

    for input_text, desc, expected_status in test_cases:
        response = client.post(
            "/api/v1/chat/ask", json={"text": input_text}, headers=headers
        )
        assert response.status_code == expected_status, f"실패: {desc}"
        assert "detail" in response.json() or "error" in response.json()


@patch("openai.resources.chat.completions.Completions.create")
def test_cache_functionality(
    mock_openai: Any, mock_openai_response: ChatCompletion
) -> None:
    """캐시 기능 테스트"""
    response_cache.clear()
    headers = {"X-API-Key": get_settings().API_KEY}
    test_question = "캐시 테스트 질문"

    # 첫 번째 요청 - mock을 사용하여 응답 설정
    mock_openai.return_value = mock_openai_response
    mock_openai.reset_mock()  # Reset the mock to clear any previous calls
    
    response1 = client.post(
        "/api/v1/chat/ask", json={"text": test_question}, headers=headers
    )
    assert response1.status_code == 200
    assert mock_openai.call_count == 1  # Should call OpenAI API

    # 캐시된 응답 확인
    response2 = client.post(
        "/api/v1/chat/ask", json={"text": test_question}, headers=headers
    )
    assert response2.status_code == 200
    assert mock_openai.call_count == 1  # Should NOT call OpenAI API again
    assert response2.json()["response"] == response1.json()["response"]


def test_session_management() -> None:
    """세션 관리 테스트"""
    session_id = session_manager.create_session()  # Create session first
    headers = {"X-API-Key": get_settings().API_KEY}

    # 세션 생성 및 메시지 추가
    session_manager.add_message(session_id, "user", "테스트 메시지")

    # 세션 조회
    response = client.get(f"/api/v1/chat/conversation/{session_id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data["conversation"]) > 0

    # 세션 삭제
    response = client.delete(f"/api/v1/chat/conversation/{session_id}", headers=headers)
    assert response.status_code == 204


@patch("openai.resources.chat.completions.Completions.create")
def test_error_handling(mock_openai: Any) -> None:
    """오류 처리 테스트"""
    headers = {"X-API-Key": get_settings().API_KEY}

    # API 오류
    mock_openai.side_effect = AIServiceException("API 오류")
    response = client.post(
        "/api/v1/chat/ask", json={"text": "오류 테스트"}, headers=headers
    )
    assert response.status_code == 500
    assert "error" in response.json()

    # 타임아웃
    mock_openai.side_effect = TimeoutError()
    response = client.post(
        "/api/v1/chat/ask", json={"text": "타임아웃 테스트"}, headers=headers
    )
    assert response.status_code == 504
    assert "error" in response.json()


@pytest.mark.asyncio
async def test_metrics() -> None:
    """메트릭스 테스트"""
    # 기본 메트릭스 테스트
    with patch("core.middleware.REQUEST_COUNT") as mock_counter:
        response = client.get("/")
        assert response.status_code == 200
        mock_counter.labels.assert_called_once()
        mock_counter.labels().inc.assert_called_once()

    # 내부 접근 테스트
    with patch("fastapi.Request") as mock_request:
        mock_request.client.host = "127.0.0.1"
        response = client.get("/metrics")
        assert response.status_code == 200
        assert "request_count" in response.text

    # 외부 접근 테스트
    response = client.get("/metrics")
    assert response.status_code == 403
