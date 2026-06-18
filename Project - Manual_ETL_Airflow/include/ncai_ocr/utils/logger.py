from logging import handlers
from functools import wraps
from datetime import datetime

import logging, fitz, os, warnings

warnings.filterwarnings('ignore')

# 로그 디렉토리 확인 및 생성
LOG_DIR = './logs'
if not os.path.isdir(LOG_DIR):
    os.makedirs(LOG_DIR)

def setup_logger(logger_name, log_file_suffix):
    """
    로거 셋업 함수
    """
    now_date = datetime.now().strftime("%Y-%m-%d")
    log_file_path = os.path.join(LOG_DIR, f"{log_file_suffix}_{now_date}.log")

    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)

    # 핸들러 중복 방지
    if not logger.handlers:
        file_handler = handlers.TimedRotatingFileHandler(
            log_file_path,
            when='midnight',
            interval=1,
            encoding='utf-8'
        )
        formatter = logging.Formatter('%(asctime)s - %(name)s - [%(levelname)s] - %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def apply_logger(logger_name, log_file_suffix='app'):
    """
    로거 데코레이터 함수
    """
    target_logger = setup_logger(logger_name, log_file_suffix)

    def log_decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                # 에러 발생 시 상세 정보(exc_info=True) 로깅
                target_logger.error(f"Function '{func.__name__}' failed: {e}", exc_info=True)
                raise
        return wrapper
    return log_decorator