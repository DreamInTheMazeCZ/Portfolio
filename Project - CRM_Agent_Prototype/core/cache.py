from typing import Any, Optional, Dict
import time
from datetime import timedelta
import hashlib
import json
import logging
from collections import OrderedDict

logger = logging.getLogger(__name__)

class ResponseCache:
    def __init__(self, ttl_seconds: int = 3600, max_size: int = 1000):
        self._cache: OrderedDict[str, tuple[Any, float]] = OrderedDict()
        self._ttl_seconds = ttl_seconds
        self._max_size = max_size

    def _generate_key(self, question: str) -> str:
        # SHA-256 사용하여 보안 강화
        normalized_question = question.strip().lower()
        return hashlib.sha256(normalized_question.encode('utf-8')).hexdigest()

    def _validate_response(self, response: Any) -> bool:
        try:
            if not isinstance(response, dict):
                return False
            required_fields = ["response", "metrics"]
            return all(field in response for field in required_fields)
        except Exception:
            return False

    def get(self, question: str) -> Optional[Any]:
        try:
            key = self._generate_key(question)
            if key in self._cache:
                value, timestamp = self._cache[key]
                if time.time() - timestamp <= self._ttl_seconds:
                    if self._validate_response(value):
                        # LRU 캐시 업데이트
                        self._cache.move_to_end(key)
                        return value
                # 유효하지 않은 데이터나 만료된 항목 삭제
                del self._cache[key]
                logger.debug(f"Cache entry removed: expired or invalid")
        except Exception as e:
            logger.error(f"Cache get error: {str(e)}")
        return None

    def set(self, question: str, response: Any) -> None:
        try:
            if not self._validate_response(response):
                logger.warning("Invalid response format, not caching")
                return

            key = self._generate_key(question)
            
            # 캐시 크기 제한 확인 및 관리 (LRU 방식)
            if len(self._cache) >= self._max_size:
                # 가장 오래 사용되지 않은 항목 제거
                self._cache.popitem(last=False)
                logger.debug("Cache full, removed least recently used entry")

            # 새 항목 추가 (자동으로 가장 최근에 사용된 위치로)
            self._cache[key] = (response, time.time())
            self._cache.move_to_end(key)
        except Exception as e:
            logger.error(f"Cache set error: {str(e)}")

    def clear(self) -> None:
        try:
            self._cache.clear()
        except Exception as e:
            logger.error(f"Cache clear error: {str(e)}")

    def cleanup_expired(self) -> None:
        try:
            current_time = time.time()
            expired_keys = [
                key for key, (_, timestamp) in self._cache.items()
                if current_time - timestamp > self._ttl_seconds
            ]
            for key in expired_keys:
                del self._cache[key]
            if expired_keys:
                logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
        except Exception as e:
            logger.error(f"Cache cleanup error: {str(e)}")

    def get_stats(self) -> Dict[str, int]:
        """캐시 상태 통계를 반환합니다."""
        current_time = time.time()
        active_entries = sum(1 for _, timestamp in self._cache.values() 
                           if current_time - timestamp <= self._ttl_seconds)
        return {
            "total_entries": len(self._cache),
            "active_entries": active_entries,
            "expired_entries": len(self._cache) - active_entries
        }

# 전역 캐시 인스턴스 생성
response_cache = ResponseCache()