import time
import json
from typing import Optional, Dict
from utils.logger import get_logger
from core.upbit_client import UpbitClient

logger = get_logger(__name__)

class Executor:
    """자산별 주문 실행기"""
    
    def __init__(self, symbol: str, trade_amount: float, dry_run: bool = True, use_upbit: bool = False):
        self.symbol = symbol
        self.trade_amount = trade_amount
        self.dry_run = dry_run
        self.use_upbit = use_upbit
        self.order_history = []
        self.last_order_time = 0
        self.min_order_interval = 30  # 최소 주문 간격 (초)
        
        # 업비트 설정 로드
        if use_upbit:
            self._load_upbit_config()
    
    def _load_upbit_config(self):
        """업비트 설정 로드"""
        try:
            with open('config/upbit_config.json', 'r', encoding='utf-8') as f:
                self.upbit_config = json.load(f)
            
            # 실제 거래용 업비트 클라이언트
            if (self.upbit_config.get('access_key') != 'YOUR_UPBIT_ACCESS_KEY' and 
                self.upbit_config.get('secret_key') != 'YOUR_UPBIT_SECRET_KEY' and 
                not self.dry_run):
                self.upbit_client = UpbitClient(
                    self.upbit_config['access_key'],
                    self.upbit_config['secret_key']
                )
                logger.info(f"[{self.symbol}] 업비트 실제 거래 모드 활성화")
            else:
                self.upbit_client = None
                logger.info(f"[{self.symbol}] 모의거래 모드")
                
        except Exception as e:
            logger.error(f"업비트 설정 로드 실패: {e}")
            self.upbit_config = {}
            self.upbit_client = None
    
    def _can_place_order(self) -> bool:
        """주문 가능 여부 체크"""
        current_time = time.time()
        if current_time - self.last_order_time < self.min_order_interval:
            logger.warning(f"[{self.symbol}] 주문 간격 부족: {self.min_order_interval}초 대기 필요")
            return False
        return True
    
    def _simulate_order(self, order_type: str, quantity: float, price: float) -> Dict:
        """시뮬레이션 주문 (실제 거래소 연동시 이 부분을 실제 API 호출로 교체)"""
        order = {
            "id": f"sim_{int(time.time())}",
            "symbol": self.symbol,
            "type": order_type,
            "quantity": quantity,
            "price": price,
            "status": "filled",
            "timestamp": time.time()
        }
        return order
    
    def buy(self, price: float) -> Optional[Dict]:
        """매수 주문 실행"""
        if not self._can_place_order():
            return None
        
        try:
            quantity = self.trade_amount
            
            if self.dry_run:
                order = self._simulate_order("buy", quantity, price)
                logger.info(f"[{self.symbol}] 모의 매수: {quantity:.6f} @ ${price:.4f}")
            else:
                # 실제 거래소 API 호출
                order = self._place_real_order("buy", quantity, price)
                logger.info(f"[{self.symbol}] 실제 매수: {quantity:.6f} @ ${price:.4f}")
            
            self.order_history.append(order)
            self.last_order_time = time.time()
            return order
            
        except Exception as e:
            logger.error(f"[{self.symbol}] 매수 주문 실패: {e}")
            return None
    
    def sell(self, quantity: float, price: float) -> Optional[Dict]:
        """매도 주문 실행"""
        if not self._can_place_order():
            return None
        
        try:
            if self.dry_run:
                order = self._simulate_order("sell", quantity, price)
                logger.info(f"[{self.symbol}] 모의 매도: {quantity:.6f} @ ${price:.4f}")
            else:
                # 실제 거래소 API 호출
                order = self._place_real_order("sell", quantity, price)
                logger.info(f"[{self.symbol}] 실제 매도: {quantity:.6f} @ ${price:.4f}")
            
            self.order_history.append(order)
            self.last_order_time = time.time()
            return order
            
        except Exception as e:
            logger.error(f"[{self.symbol}] 매도 주문 실패: {e}")
            return None
    
    def _place_real_order(self, order_type: str, quantity: float, price: float) -> Dict:
        """실제 거래소 주문"""
        if not self.upbit_client:
            raise Exception("업비트 클라이언트가 초기화되지 않음")
        
        # 심볼을 업비트 마켓으로 변환
        upbit_market = self.upbit_config.get('market_mapping', {}).get(self.symbol)
        if not upbit_market:
            raise Exception(f"업비트 마켓 매핑을 찾을 수 없음: {self.symbol}")
        
        # 업비트 주문 실행
        side = 'bid' if order_type == 'buy' else 'ask'
        
        if order_type == 'buy':
            # 매수: 금액 기준으로 주문 (시장가)
            order_amount = quantity * price
            min_amount = self.upbit_config.get('min_order_amounts', {}).get(upbit_market, 5000)
            
            if order_amount < min_amount:
                logger.warning(f"최소 주문 금액 미달: {order_amount} < {min_amount}")
                order_amount = min_amount
            
            # 원화 마켓에서는 주문 금액을 price 파라미터에 전달
            result = self.upbit_client.place_order(
                market=upbit_market,
                side=side,
                ord_type='price',  # 시장가 매수
                price=order_amount
            )
        else:
            # 매도: 수량 기준으로 주문
            result = self.upbit_client.place_order(
                market=upbit_market,
                side=side,
                ord_type='market',  # 시장가 매도
                volume=quantity
            )
        
        if result:
            return {
                "id": result.get('uuid', ''),
                "symbol": self.symbol,
                "type": order_type,
                "quantity": quantity,
                "price": price,
                "status": "filled",
                "timestamp": time.time(),
                "exchange_result": result
            }
        else:
            raise Exception("주문 실행 실패")
    
    def cancel_all_orders(self):
        """모든 미체결 주문 취소"""
        if self.dry_run:
            logger.info(f"[{self.symbol}] 모의 주문 취소")
        else:
            # 실제 주문 취소 로직
            pass
    
    def get_order_history(self) -> list:
        """주문 히스토리 반환"""
        return self.order_history.copy()
    
    def get_last_order(self) -> Optional[Dict]:
        """마지막 주문 정보 반환"""
        return self.order_history[-1] if self.order_history else None 