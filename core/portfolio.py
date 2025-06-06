from typing import Optional
from utils.logger import get_logger

logger = get_logger(__name__)

class Portfolio:
    """자산별 포트폴리오 관리"""
    
    def __init__(self, symbol: str):
        self.symbol = symbol
        self.holdings = 0.0  # 보유 수량
        self.avg_price = 0.0  # 평균 매수 단가
        self.total_cost = 0.0  # 총 매수 금액
        self.total_sold = 0.0  # 총 매도 금액
        self.trades_count = 0  # 거래 횟수
    
    def add_buy(self, quantity: float, price: float):
        """매수 거래 추가"""
        cost = quantity * price
        
        # 평균 단가 계산
        if self.holdings > 0:
            self.total_cost += cost
            self.avg_price = self.total_cost / (self.holdings + quantity)
        else:
            self.avg_price = price
            self.total_cost = cost
        
        self.holdings += quantity
        self.trades_count += 1
        
        logger.info(f"[{self.symbol}] 매수: {quantity:.6f} @ ${price:.4f}, 평균단가: ${self.avg_price:.4f}")
    
    def add_sell(self, quantity: float, price: float):
        """매도 거래 추가"""
        if self.holdings < quantity:
            logger.warning(f"[{self.symbol}] 매도 수량 부족: 보유 {self.holdings:.6f} < 매도 {quantity:.6f}")
            return False
        
        sold_amount = quantity * price
        sold_cost = quantity * self.avg_price
        
        self.holdings -= quantity
        self.total_sold += sold_amount
        self.total_cost -= sold_cost
        self.trades_count += 1
        
        profit = sold_amount - sold_cost
        profit_rate = (profit / sold_cost) * 100 if sold_cost > 0 else 0
        
        logger.info(f"[{self.symbol}] 매도: {quantity:.6f} @ ${price:.4f}, 수익: ${profit:.2f} ({profit_rate:.2f}%)")
        return True
    
    def get_current_value(self, current_price: float) -> float:
        """현재 가치 계산"""
        return self.holdings * current_price
    
    def get_profit_loss(self, current_price: float) -> tuple:
        """현재 손익 계산 (금액, 수익률)"""
        if self.holdings == 0:
            return 0.0, 0.0
        
        current_value = self.get_current_value(current_price)
        remaining_cost = self.holdings * self.avg_price
        profit = current_value - remaining_cost
        profit_rate = (profit / remaining_cost) * 100 if remaining_cost > 0 else 0
        
        return profit, profit_rate
    
    def get_status(self, current_price: Optional[float] = None) -> dict:
        """포트폴리오 현황 반환"""
        status = {
            "symbol": self.symbol,
            "holdings": self.holdings,
            "avg_price": self.avg_price,
            "total_cost": self.total_cost,
            "trades_count": self.trades_count
        }
        
        if current_price and self.holdings > 0:
            profit, profit_rate = self.get_profit_loss(current_price)
            status.update({
                "current_price": current_price,
                "current_value": self.get_current_value(current_price),
                "profit": profit,
                "profit_rate": profit_rate
            })
        
        return status 