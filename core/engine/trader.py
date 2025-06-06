import time
from typing import Dict, Optional
from core.data_collector import DataCollector
from core.portfolio import Portfolio
from core.trigger import Trigger
from core.executor import Executor
from core.notifier import Notifier
from core.config import config
from utils.logger import get_logger

logger = get_logger(__name__)

class TraderEngine:
    """자산별 독립 트레이딩 엔진"""
    
    def __init__(self, asset_config: Dict, dry_run: bool = None):
        self.symbol = asset_config["symbol"]
        self.base_currency = asset_config["base_currency"]
        self.quote_currency = asset_config["quote_currency"]
        self.trade_amount = asset_config["trade_amount"]
        # 환경변수에서 dry_run 설정 가져오기
        self.dry_run = dry_run if dry_run is not None else config.dry_run
        
        # 모듈 인스턴스 초기화 (업비트 전용)
        self.data_collector = DataCollector()
        self.portfolio = Portfolio(self.symbol)
        self.trigger = Trigger(self.symbol)
        self.executor = Executor(self.symbol, self.trade_amount, self.dry_run, use_upbit=True)
        self.notifier = Notifier(self.symbol)
        
        # 상태 변수
        self.is_running = False
        self.last_run_time = 0
        self.run_count = 0
        self.error_count = 0
        
        logger.info(f"[{self.symbol}] 트레이딩 엔진 초기화 완료")
    
    def get_current_price(self) -> Optional[float]:
        """현재 가격 조회"""
        return self.data_collector.get_price(self.symbol)
    
    def run_once(self) -> bool:
        """한번의 트레이딩 사이클 실행"""
        try:
            self.run_count += 1
            current_time = time.time()
            
            # 현재 가격 조회
            current_price = self.get_current_price()
            if current_price is None:
                logger.warning(f"[{self.symbol}] 가격 조회 실패")
                return False
            
            # 매매 시그널 판단
            action = self.trigger.check(current_price, self.portfolio)
            
            if action == "buy":
                self._execute_buy(current_price)
            elif action == "sell":
                self._execute_sell(current_price)
            else:
                logger.debug(f"[{self.symbol}] 대기: ${current_price:.4f}")
            
            self.last_run_time = current_time
            return True
            
        except Exception as e:
            self.error_count += 1
            logger.error(f"[{self.symbol}] 실행 오류: {e}")
            self.notifier.send_error_notification(str(e))
            return False
    
    def _execute_buy(self, price: float):
        """매수 실행"""
        try:
            order = self.executor.buy(price)
            if order:
                # 포트폴리오 업데이트
                quantity = order["quantity"]
                self.portfolio.add_buy(quantity, price)
                
                # 알림 전송
                portfolio_status = self.portfolio.get_status(price)
                self.notifier.send_trade_notification(order, portfolio_status)
                
                logger.info(f"[{self.symbol}] 매수 완료: {quantity:.6f} @ ${price:.4f}")
                
        except Exception as e:
            logger.error(f"[{self.symbol}] 매수 실행 실패: {e}")
            self.notifier.send_error_notification(f"매수 실행 실패: {e}")
    
    def _execute_sell(self, price: float):
        """매도 실행"""
        try:
            # 보유량의 일부만 매도
            sell_ratio = self.trigger.config.get("sell_ratio", 1.0)
            quantity = self.portfolio.holdings * sell_ratio
            if quantity > 0:
                order = self.executor.sell(quantity, price)
                if order:
                    # 포트폴리오 업데이트
                    success = self.portfolio.add_sell(quantity, price)
                    if success:
                        # 알림 전송
                        portfolio_status = self.portfolio.get_status(price)
                        self.notifier.send_trade_notification(order, portfolio_status)
                        
                        logger.info(f"[{self.symbol}] 매도 완료: {quantity:.6f} @ ${price:.4f}")
                    
        except Exception as e:
            logger.error(f"[{self.symbol}] 매도 실행 실패: {e}")
            self.notifier.send_error_notification(f"매도 실행 실패: {e}")
    
    def get_status(self) -> Dict:
        """엔진 상태 정보 반환"""
        current_price = self.get_current_price()
        portfolio_status = self.portfolio.get_status(current_price)
        
        status = {
            "symbol": self.symbol,
            "is_running": self.is_running,
            "run_count": self.run_count,
            "error_count": self.error_count,
            "last_run_time": self.last_run_time,
            "current_price": current_price,
            "portfolio": portfolio_status,
            "last_action": self.trigger.last_action,
            "signal_strength": self.trigger.get_signal_strength(current_price) if current_price else 0
        }
        
        return status
    
    def start(self):
        """엔진 시작"""
        self.is_running = True
        logger.info(f"[{self.symbol}] 트레이딩 엔진 시작")
    
    def stop(self):
        """엔진 중지"""
        self.is_running = False
        # 미체결 주문 취소
        self.executor.cancel_all_orders()
        logger.info(f"[{self.symbol}] 트레이딩 엔진 중지")
    
    def send_status_notification(self):
        """상태 알림 전송"""
        current_price = self.get_current_price()
        if current_price:
            portfolio_status = self.portfolio.get_status(current_price)
            self.notifier.send_status_notification(portfolio_status, current_price) 