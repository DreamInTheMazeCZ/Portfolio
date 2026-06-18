# 필요한 모듈들을 임포트합니다.
from typing import Any, Dict, Optional, List
from datetime import datetime
import uuid
import hashlib
import re
import html
from pydantic import BaseModel
import tiktoken
from core.settings import get_settings
import secrets
import string
import json

# 환경 설정을 가져옵니다.
app_settings = get_settings()

# 보안을 위한 상수 정의
ALLOWED_CHARS = string.ascii_letters + string.digits + "-_"
SESSION_ID_PATTERN = re.compile(r'^[a-zA-Z0-9\-_]{1,64}$')
HTML_TAG_PATTERN = re.compile(r'<[^>]*?>')
SCRIPT_PATTERN = re.compile(r'<script.*?>.*?</script>', re.IGNORECASE | re.DOTALL)
SENSITIVE_PATTERN = re.compile(r'(password|token|key|secret|auth)', re.IGNORECASE)

def generate_secure_random_string(length: int = 32) -> str:
    """
    암호학적으로 안전한 랜덤 문자열을 생성합니다.
    
    Args:
        length (int): 생성할 문자열의 길이
        
    Returns:
        str: 생성된 랜덤 문자열
    """
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def validate_password(password: str, app_config: Any) -> tuple[bool, str]:
    """비밀번호 정책 검증"""
    if len(password) < app_config.PASSWORD_POLICY["min_length"]:
        return False, f"비밀번호는 최소 {app_config.PASSWORD_POLICY['min_length']}자 이상이어야 합니다"
    
    if app_config.PASSWORD_POLICY["require_uppercase"] and not any(c.isupper() for c in password):
        return False, "비밀번호에는 대문자가 포함되어야 합니다"
    
    if app_config.PASSWORD_POLICY["require_lowercase"] and not any(c.islower() for c in password):
        return False, "비밀번호에는 소문자가 포함되어야 합니다"
    
    if app_config.PASSWORD_POLICY["require_numbers"] and not any(c.isdigit() for c in password):
        return False, "비밀번호에는 숫자가 포함되어야 합니다"
    
    if app_config.PASSWORD_POLICY["require_special_chars"] and not any(not c.isalnum() for c in password):
        return False, "비밀번호에는 특수문자가 포함되어야 합니다"
    
    return True, ""

def validate_session_id(session_id: str) -> bool:
    """세션 ID 검증"""
    # 길이 제한
    if len(session_id) > 64:
        return False
    
    # 허용된 문자만 포함되었는지 확인
    if not SESSION_ID_PATTERN.match(session_id):
        return False
    
    return True

def sanitize_input(text: str) -> str:
    """사용자 입력을 안전하게 정제"""
    if not text or not text.strip():
        return ""
        
    settings = get_settings()
    
    # 허용된 문자만 포함되었는지 검사
    allowed_pattern = re.compile(f"^[{settings.INPUT_VALIDATION['allowed_characters']}]*$")
    if not allowed_pattern.match(text):
        raise ValueError("허용되지 않은 문자가 포함되어 있습니다")
    
    # 길이 제한 검사
    if len(text) > settings.INPUT_VALIDATION["max_question_length"]:
        raise ValueError(f"입력 길이가 제한({settings.INPUT_VALIDATION['max_question_length']}자)을 초과했습니다")
    
    # 악성 패턴 검사
    for pattern in settings.INPUT_VALIDATION["blocked_patterns"]:
        if re.search(pattern, text, re.IGNORECASE):
            raise ValueError("악성 코드가 감지되었습니다")
    
    # HTML 태그 제거
    text = HTML_TAG_PATTERN.sub('', text)
    # XSS 스크립트 제거
    text = SCRIPT_PATTERN.sub('', text)
    # HTML 엔티티 이스케이프
    text = html.escape(text)
    
    return text.strip()

def secure_random_string(length: int = 32, use_punctuation: bool = False) -> str:
    """암호학적으로 안전한 랜덤 문자열 생성"""
    if length < 8:
        raise ValueError("보안을 위해 최소 8자 이상이어야 합니다")
    
    alphabet = string.ascii_letters + string.digits
    if use_punctuation:
        alphabet += string.punctuation
        
    while True:
        password = ''.join(secrets.choice(alphabet) for _ in range(length))
        # 각 문자 종류가 최소 1개 이상 포함되었는지 확인
        if (any(c.islower() for c in password) and
            any(c.isupper() for c in password) and
            any(c.isdigit() for c in password) and
            (not use_punctuation or any(c in string.punctuation for c in password))):
            break
    
    return password

def hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
    """
    비밀번호를 안전하게 해시화
    - Argon2id 사용 (OWASP 권장)
    """
    from argon2 import PasswordHasher
    from base64 import b64encode
    
    if salt is None:
        salt = b64encode(secrets.token_bytes(16)).decode('utf-8')
    
    ph = PasswordHasher()
    password_hash = ph.hash(password + salt)
    return password_hash, salt

def hash_sensitive_data(data: str) -> str:
    """
    민감한 데이터를 안전하게 해시화합니다.
    
    Args:
        data (str): 해시화할 데이터
        
    Returns:
        str: 해시화된 문자열
    """
    salt = generate_secure_random_string(16)
    return hashlib.blake2b(
        (data + salt).encode(), 
        digest_size=32
    ).hexdigest()

def mask_sensitive_info(text: str) -> str:
    """
    로그나 오류 메시지에서 민감한 정보를 마스킹합니다.
    
    Args:
        text (str): 처리할 텍스트
        
    Returns:
        str: 마스킹된 텍스트
    """
    return SENSITIVE_PATTERN.sub('[REDACTED]', text)

def sanitize_log_content(content: str, max_length: int = 100) -> str:
    """
    로그에 기록될 내용을 안전하게 처리합니다.
    
    다음과 같은 처리를 수행합니다:
    - 민감한 정보 마스킹
    - HTML/스크립트 제거
    - 길이 제한
    
    Args:
        content (str): 처리할 내용
        max_length (int): 최대 허용 길이
        
    Returns:
        str: 안전하게 처리된 문자열
    """
    if not content:
        return ""
        
    # 민감한 정보 패턴
    patterns = [
        (r'api[-_]key["\']?\s*[:=]\s*["\']?[\w\-]+["\']?', '[API_KEY_MASKED]'),
        (r'password["\']?\s*[:=]\s*["\']?[\w\-]+["\']?', '[PASSWORD_MASKED]'),
        (r'token["\']?\s*[:=]\s*["\']?[\w\-]+["\']?', '[TOKEN_MASKED]'),
        (r'secret["\']?\s*[:=]\s*["\']?[\w\-]+["\']?', '[SECRET_MASKED]'),
        (r'auth["\']?\s*[:=]\s*["\']?[\w\-]+["\']?', '[AUTH_MASKED]'),
        (r'bearer\s+[\w\-\.]+', '[BEARER_TOKEN_MASKED]'),
        (r'\b[\w\.-]+@[\w\.-]+\.\w+\b', '[EMAIL_MASKED]'),
        (r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', '[IP_MASKED]')
    ]
    
    result = content
    for pattern, mask in patterns:
        result = re.sub(pattern, mask, result, flags=re.IGNORECASE)
    
    # HTML 태그 및 스크립트 제거
    result = HTML_TAG_PATTERN.sub('', result)
    result = SCRIPT_PATTERN.sub('', result)
    
    # 긴 내용 축약
    if len(result) > max_length:
        return result[:max_length] + "..."
        
    return result

class SecureRequestContext(BaseModel):
    """
    보안이 강화된 요청 컨텍스트 정보를 담는 클래스입니다.
    """
    request_id: str = str(uuid.uuid4())
    timestamp: datetime = datetime.now()
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    
    @property
    def context_dict(self) -> Dict[str, Any]:
        """컨텍스트 정보를 딕셔너리 형태로 반환합니다.""" 
        data = self.dict()
        # 민감한 정보 마스킹
        if self.user_id:
            data['user_id'] = mask_sensitive_info(self.user_id)
        return data

def generate_session_id(user_id: str) -> str:
    """
    사용자 ID를 기반으로 고유한 세션 ID를 생성합니다.
    
    세션 ID는 사용자 ID와 현재 시각을 조합하여 SHA-256 해시로 생성됩니다.
    이는 예측 불가능하고 충돌 가능성이 매우 낮은 고유한 값을 보장합니다.
    
    Args:
        user_id (str): 사용자의 고유 식별자
        
    Returns:
        str: 32자리 16진수 문자열로 된 세션 ID
    """
    timestamp = datetime.now().isoformat()
    unique_string = f"{user_id}-{timestamp}"
    return hashlib.sha256(unique_string.encode()).hexdigest()[:32]

def format_error_message(error: Exception, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    오류 메시지를 일관된 형식으로 포맷팅합니다.
    
    이 함수는 다음 정보를 포함하는 오류 상세 정보를 생성합니다:
    - 오류 유형
    - 오류 메시지
    - 발생 시각
    - 추가 컨텍스트 정보 (있는 경우)
    
    Args:
        error (Exception): 발생한 예외 객체
        context (Dict[str, Any], optional): 추가적인 컨텍스트 정보
        
    Returns:
        Dict[str, Any]: 포맷팅된 오류 정보
    """
    error_detail = {
        "error_type": type(error).__name__,
        "error_message": str(error),
        "timestamp": datetime.now().isoformat()
    }
    
    if context is not None:
        error_detail["context"] = json.dumps(context)
        
    return error_detail

def count_tokens(messages: List[Dict[str, str]]) -> int:
    """OpenAI API 메시지의 토큰 수를 계산합니다."""
    encoding = tiktoken.encoding_for_model(app_settings.OPENAI_MODEL)
    num_tokens = 0
    
    for message in messages:
        num_tokens += 3
        for key, value in message.items():
            num_tokens += len(encoding.encode(value))
            if key == "role":
                num_tokens += 1
    
    num_tokens += 3
    return num_tokens

def calculate_token_metrics(prompt: str, response: str) -> Dict[str, int]:
    """프롬프트와 응답의 토큰 사용량을 계산합니다."""
    encoding = tiktoken.encoding_for_model(app_settings.OPENAI_MODEL)
    prompt_tokens = len(encoding.encode(prompt))
    completion_tokens = len(encoding.encode(response))
    
    return {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": prompt_tokens + completion_tokens
    }