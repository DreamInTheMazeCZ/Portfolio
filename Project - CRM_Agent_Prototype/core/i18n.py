import json
import os
from typing import Dict, Any
from functools import lru_cache
from core.settings import get_settings

settings = get_settings()

class I18n:
    def __init__(self, language: str = settings.DEFAULT_LANGUAGE):
        self.language = language
        self.messages = self._load_messages()

    def _load_messages(self) -> Dict[str, Any]:
        """언어 리소스 파일을 로드합니다."""
        file_path = os.path.join(
            settings.RESOURCES_PATH,
            f"{self.language}.json"
        )
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load language file {file_path}: {e}")
            return {}

    def get(self, key: str, **kwargs) -> str:
        """
        주어진 키에 해당하는 메시지를 반환합니다.
        중첩된 키는 점(.)으로 구분합니다.
        예: i18n.get("errors.not_found")
        """
        try:
            value = self.messages
            for k in key.split('.'):
                value = value[k]
            
            if kwargs:
                return value.format(**kwargs)
            return value
        except (KeyError, AttributeError):
            return key

@lru_cache()
def get_i18n() -> I18n:
    """I18n 인스턴스를 생성하고 캐시합니다."""
    return I18n()