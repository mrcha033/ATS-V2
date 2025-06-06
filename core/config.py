import os
from dotenv import load_dotenv
from typing import Optional
from utils.logger import get_logger

logger = get_logger(__name__)

class Config:
    """환경변수 기반 설정 관리"""
    
    def __init__(self):
        # .env 파일 로드
        load_dotenv()
        self._validate_required_env()
        logger.info("환경변수 설정 로드 완료")
    
    def _validate_required_env(self):
        """필수 환경변수 검증"""
        required_vars = ['UPBIT_ACCESS_KEY', 'UPBIT_SECRET_KEY']
        missing_vars = []
        
        for var in required_vars:
            if not os.getenv(var) or os.getenv(var) == 'your_upbit_access_key_here' or os.getenv(var) == 'your_upbit_secret_key_here':
                missing_vars.append(var)
        
        if missing_vars:
            logger.warning(f"업비트 API 키가 설정되지 않음: {missing_vars}")
            logger.warning("모의거래 모드로만 실행됩니다")
    
    @property
    def upbit_access_key(self) -> Optional[str]:
        """업비트 Access Key"""
        key = os.getenv('UPBIT_ACCESS_KEY')
        if key and key != 'your_upbit_access_key_here':
            return key
        return None
    
    @property
    def upbit_secret_key(self) -> Optional[str]:
        """업비트 Secret Key"""
        key = os.getenv('UPBIT_SECRET_KEY')
        if key and key != 'your_upbit_secret_key_here':
            return key
        return None
    
    @property
    def dry_run(self) -> bool:
        """모의거래 모드 여부"""
        return os.getenv('DRY_RUN', 'true').lower() == 'true'
    
    @property
    def log_level(self) -> str:
        """로그 레벨"""
        return os.getenv('LOG_LEVEL', 'INFO').upper()
    
    @property
    def polling_interval(self) -> int:
        """폴링 간격 (초)"""
        return int(os.getenv('POLLING_INTERVAL', '10'))
    
    @property
    def status_update_interval(self) -> int:
        """상태 업데이트 간격 (초)"""
        return int(os.getenv('STATUS_UPDATE_INTERVAL', '300'))

    @property
    def max_workers(self) -> Optional[int]:
        """병렬 실행 스레드 수"""
        value = os.getenv('MAX_WORKERS')
        return int(value) if value and value.isdigit() else None
    
    @property
    def discord_webhook_url(self) -> Optional[str]:
        """Discord 웹훅 URL"""
        url = os.getenv('DISCORD_WEBHOOK_URL')
        return url if url and url.strip() else None
    
    @property
    def slack_webhook_url(self) -> Optional[str]:
        """Slack 웹훅 URL"""
        url = os.getenv('SLACK_WEBHOOK_URL')
        return url if url and url.strip() else None
    
    @property
    def has_api_keys(self) -> bool:
        """API 키가 올바르게 설정되었는지 확인"""
        return self.upbit_access_key is not None and self.upbit_secret_key is not None
    
    def get_market_mapping(self) -> dict:
        """심볼-마켓 매핑"""
        return {
            "BTC/USDT": "KRW-BTC",
            "ETH/USDT": "KRW-ETH",
            "ADA/USDT": "KRW-ADA"
        }
    
    def get_min_order_amounts(self) -> dict:
        """최소 주문 금액"""
        return {
            "KRW-BTC": 5000,
            "KRW-ETH": 5000,
            "KRW-ADA": 5000
        }

# 전역 설정 인스턴스
config = Config() 