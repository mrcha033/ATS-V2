import logging
import os
from datetime import datetime

def setup_logger(name: str = "ATS_V2", level: int = logging.INFO) -> logging.Logger:
    """로거 설정"""
    
    # 로그 디렉토리 생성
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    
    # 로거 생성
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 이미 핸들러가 있으면 반환
    if logger.handlers:
        return logger
    
    # 포맷터 설정
    formatter = logging.Formatter(
        fmt='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 콘솔 핸들러
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 파일 핸들러
    log_file = os.path.join(log_dir, f"ats_v2_{datetime.now().strftime('%Y%m%d')}.log")
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger

def get_logger(name: str = "ATS_V2") -> logging.Logger:
    """로거 인스턴스 반환"""
    logger = logging.getLogger(name)
    if not logger.handlers:
        return setup_logger(name)
    return logger 