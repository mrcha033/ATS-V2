from typing import Optional
from utils.logger import get_logger

logger = get_logger(__name__)

class Trigger:
    """자산별 매매 시그널 판단기"""
    
    def __init__(self, symbol: str, config: dict = None):
        self.symbol = symbol
        self.config = config or self._default_config()
        self.price_history = []
        self.last_action = None
        self.last_action_price = None
    
    def _default_config(self) -> dict:
        """기본 설정"""
        return {
            "buy_drop_threshold": -0.02,  # 2% 하락시 매수
            "sell_profit_threshold": 0.0,  # 평단가 이상이면 매도
            "sell_ratio": 0.2,  # 매도 비율
            "min_interval_minutes": 5,  # 최소 거래 간격
            "max_position_ratio": 0.8  # 최대 포지션 비율
        }
    
    def update_price(self, price: float):
        """가격 히스토리 업데이트"""
        self.price_history.append(price)
        # 최근 100개만 유지
        if len(self.price_history) > 100:
            self.price_history.pop(0)
    
    def check_buy_signal(self, current_price: float, portfolio) -> bool:
        """매수 시그널 체크"""
        if len(self.price_history) < 10:
            return False
        
        # 최근 가격 대비 하락률 계산
        recent_high = max(self.price_history[-10:])
        drop_rate = (current_price - recent_high) / recent_high
        
        # 하락 임계값 체크
        if drop_rate <= self.config["buy_drop_threshold"]:
            logger.info(f"[{self.symbol}] 매수 시그널: {drop_rate:.2%} 하락")
            return True
        
        return False
    
    def check_sell_signal(self, current_price: float, portfolio) -> bool:
        """매도 시그널 체크"""
        if portfolio.holdings <= 0:
            return False
        
        profit, profit_rate = portfolio.get_profit_loss(current_price)
        
        # 수익 실현 체크 (평단가 이상)
        if profit_rate >= self.config["sell_profit_threshold"] * 100:
            logger.info(f"[{self.symbol}] 매도 시그널: {profit_rate:.2f}% 수익")
            return True

        return False
    
    def check(self, current_price: float, portfolio) -> Optional[str]:
        """매매 시그널 종합 판단"""
        if current_price is None:
            return None
        
        self.update_price(current_price)
        
        # 매도 우선 체크
        if self.check_sell_signal(current_price, portfolio):
            self.last_action = "sell"
            self.last_action_price = current_price
            return "sell"
        
        # 매수 체크
        if self.check_buy_signal(current_price, portfolio):
            self.last_action = "buy"
            self.last_action_price = current_price
            return "buy"
        
        return "hold"
    
    def get_signal_strength(self, current_price: float) -> float:
        """시그널 강도 반환 (0-1)"""
        if len(self.price_history) < 10:
            return 0.0
        
        recent_high = max(self.price_history[-10:])
        recent_low = min(self.price_history[-10:])
        
        if recent_high == recent_low:
            return 0.0
        
        # 현재 가격의 상대적 위치
        position = (current_price - recent_low) / (recent_high - recent_low)
        return 1.0 - position  # 낮은 위치일수록 강한 매수 시그널 