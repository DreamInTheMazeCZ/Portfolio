from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
import threading
from core.utils import secure_random_string
from core.exceptions import SecurityException

logger = logging.getLogger(__name__)

class SessionManager:
    def __init__(self, max_sessions: int = 1000, max_history_per_session: int = 50, session_timeout: int = 3600):
        self._sessions: Dict[str, List[dict]] = {}
        self._session_timestamps: Dict[str, datetime] = {}
        self._session_locks: Dict[str, threading.Lock] = {}
        self.max_sessions = max_sessions
        self.max_history_per_session = max_history_per_session
        self.session_timeout = session_timeout
        self._cleanup_lock = threading.Lock()

    @staticmethod
    def _generate_session_id() -> str:
        """안전한 세션 ID 생성"""
        return secure_random_string(32)

    def _is_session_expired(self, session_id: str) -> bool:
        """세션 만료 여부 확인"""
        if session_id not in self._session_timestamps:
            return True
        last_access = self._session_timestamps[session_id]
        return datetime.now() - last_access > timedelta(seconds=self.session_timeout)

    def _acquire_session_lock(self, session_id: str) -> threading.Lock:
        """세션별 락 획득"""
        if session_id not in self._session_locks:
            self._session_locks[session_id] = threading.Lock()
        return self._session_locks[session_id]

    def create_session(self) -> str:
        """새 세션 생성"""
        session_id = self._generate_session_id()
        with self._acquire_session_lock(session_id):
            self._sessions[session_id] = []
            self._session_timestamps[session_id] = datetime.now()
            logger.info("New session created: %s", session_id)
        return session_id

    def get_session(self, session_id: str) -> List[dict]:
        """세션 데이터 조회"""
        with self._acquire_session_lock(session_id):
            if self._is_session_expired(session_id):
                self.clear_session(session_id)
                raise SecurityException(detail="세션이 만료되었습니다")
                
            if session_id not in self._sessions:
                self._sessions[session_id] = []
                self._session_timestamps[session_id] = datetime.now()
            else:
                self._session_timestamps[session_id] = datetime.now()
                
            return self._sessions[session_id].copy()

    def add_message(self, session_id: str, role: str, content: str) -> None:
        """세션에 메시지 추가"""
        with self._acquire_session_lock(session_id):
            if self._is_session_expired(session_id):
                raise SecurityException(detail="만료된 세션에는 메시지를 추가할 수 없습니다")

            if session_id not in self._sessions:
                self._sessions[session_id] = []
            
            message_size = len(content.encode('utf-8'))
            if message_size > 1024 * 1024:
                raise SecurityException(detail="메시지 크기가 너무 큽니다")
            
            self._sessions[session_id].append({
                "role": role,
                "content": content,
                "timestamp": datetime.now().isoformat()
            })
            self._session_timestamps[session_id] = datetime.now()
            
            if len(self._sessions[session_id]) > self.max_history_per_session:
                self._sessions[session_id] = self._sessions[session_id][-self.max_history_per_session:]
                logger.info("Trimmed history for session %s", session_id)

            if len(self._sessions) > self.max_sessions:
                self._cleanup_old_sessions()

    def _cleanup_old_sessions(self) -> None:
        """오래된 세션 정리"""
        with self._cleanup_lock:
            current_time = datetime.now()
            expired_sessions = [
                session_id for session_id, timestamp in self._session_timestamps.items()
                if (current_time - timestamp).total_seconds() > self.session_timeout
            ]
            
            cleanup_count = max(
                len(expired_sessions),
                len(self._sessions) - self.max_sessions
            )
            
            if cleanup_count > 0:
                sorted_sessions = sorted(
                    self._session_timestamps.items(),
                    key=lambda x: x[1]
                )
                
                sessions_to_remove = sorted_sessions[:cleanup_count]
                for session_id, _ in sessions_to_remove:
                    self.clear_session(session_id)
                    logger.info("Cleaned up old session: %s", session_id)

    def clear_session(self, session_id: str) -> None:
        """세션 삭제"""
        with self._acquire_session_lock(session_id):
            if session_id in self._sessions:
                del self._sessions[session_id]
            if session_id in self._session_timestamps:
                del self._session_timestamps[session_id]
            if session_id in self._session_locks:
                del self._session_locks[session_id]
            logger.info("Cleared session: %s", session_id)

    def get_session_stats(self) -> Dict[str, int]:
        """세션 통계 정보 반환"""
        current_time = datetime.now()
        with self._cleanup_lock:
            active_sessions = sum(
                1 for timestamp in self._session_timestamps.values()
                if (current_time - timestamp).total_seconds() <= self.session_timeout
            )
            return {
                "total_sessions": len(self._sessions),
                "active_sessions": active_sessions,
                "expired_sessions": len(self._sessions) - active_sessions
            }

# 전역 세션 매니저 인스턴스
session_manager = SessionManager()