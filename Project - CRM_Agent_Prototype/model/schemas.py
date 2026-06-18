from datetime import datetime
from enum import Enum
from typing import Any, Dict, Generic, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_validator

T = TypeVar("T")


class ResponseStatus(str, Enum):
    SUCCESS = "success"
    ERROR = "error"


class MetaData(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.now)
    process_time: Optional[float] = None
    request_id: Optional[str] = None
    version: str = "1.0.0"


class APIResponse(BaseModel, Generic[T]):
    status: ResponseStatus
    data: Optional[T] = None
    error: Optional[str] = None
    meta: MetaData = Field(default_factory=MetaData)


class Question(BaseModel):
    text: str = Field(..., min_length=1, max_length=4000, description="질문 내용")

    @field_validator("text")
    @classmethod
    def validate_text(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("질문이 비어있습니다")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "text": "파이썬으로 'Hello, World!'를 출력하는 방법을 알려주세요."
            }
        }
    )


class Message(BaseModel):
    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str = Field(..., min_length=1)
    timestamp: datetime = Field(default_factory=datetime.now)


class AIResponse(BaseModel):
    question: str
    response: Optional[str] = None
    error: Optional[str] = None
    success: bool = True
    process_time: Optional[float] = Field(None, description="처리 소요 시간(초)")
    timestamp: datetime = Field(default_factory=datetime.now)
    metrics: Dict[str, Any] = Field(
        default_factory=dict, description="성능 메트릭 데이터"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "question": "파이썬으로 'Hello, World!'를 출력하는 방법을 알려주세요.",
                "response": "print('Hello, World!')",
                "success": True,
                "process_time": 0.5,
                "timestamp": "2023-11-22T12:00:00",
                "metrics": {
                    "tokens_used": 150,
                    "prompt_tokens": 50,
                    "completion_tokens": 100,
                    "api_latency": 0.4,
                },
            }
        }
    )


class ConversationResponse(BaseModel):
    session_id: str
    messages: list[Message]
    total_messages: int
    metrics: Dict[str, Any] = Field(
        default_factory=dict, description="세션 메트릭 데이터"
    )
