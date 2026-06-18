from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import jwt
from core.settings import get_settings

settings = get_settings()

class RateLimiter:
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests: Dict[str, List[datetime]] = {}
    
    def is_allowed(self, client_id: str) -> bool:
        now = datetime.now()
        minute_ago = now - timedelta(minutes=1)
        
        # 오래된 요청 기록 정리
        if client_id in self.requests:
            self.requests[client_id] = [
                req_time for req_time in self.requests[client_id]
                if req_time > minute_ago
            ]
        else:
            self.requests[client_id] = []
        
        # 요청 수 확인
        if len(self.requests[client_id]) >= self.requests_per_minute:
            return False
        
        # 새 요청 추가
        self.requests[client_id].append(now)
        return True

class JWTAuthentication:
    def __init__(self):
        self.secret_key = settings.JWT_SECRET_KEY
        self.algorithm = "HS256"
        self.security = HTTPBearer()
        self.rate_limiter = RateLimiter()
    
    async def __call__(self, request: Request) -> Optional[str]:
        credentials: HTTPAuthorizationCredentials = await self.security(request)
        
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="인증 정보가 없습니다."
            )
        
        try:
            payload = jwt.decode(
                credentials.credentials,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            
            client_id = payload.get("sub")
            if not client_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="유효하지 않은 인증 토큰입니다."
                )
            
            # Rate limiting 체크
            if not self.rate_limiter.is_allowed(client_id):
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="요청 한도를 초과했습니다. 잠시 후 다시 시도해주세요."
                )
            
            return client_id
            
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="유효하지 않은 인증 토큰입니다."
            )

    def create_token(self, client_id: str, expires_delta: timedelta = None) -> str:
        payload = {"sub": client_id}
        if expires_delta:
            payload["exp"] = datetime.utcnow() + expires_delta
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)