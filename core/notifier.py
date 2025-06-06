import json
import time
from typing import Dict, Optional
from utils.logger import get_logger

logger = get_logger(__name__)

class Notifier:
    """자산별 거래 알림 및 로그 관리"""
    
    def __init__(self, symbol: str, config: dict = None):
        self.symbol = symbol
        self.config = config or self._default_config()
        self.notification_history = []
    
    def _default_config(self) -> dict:
        """기본 설정"""
        return {
            "enable_console": True,
            "enable_file": True,
            "enable_webhook": False,
            "log_file": f"logs/{self.symbol.replace('/', '_')}_trades.log",
            "webhook_url": None
        }
    
    def send_trade_notification(self, order: Dict, portfolio_status: Dict):
        """거래 완료 알림"""
        message = self._format_trade_message(order, portfolio_status)
        self._send_notification("TRADE", message)
    
    def send_signal_notification(self, signal: str, price: float, reason: str):
        """시그널 발생 알림"""
        message = f"[{self.symbol}] {signal.upper()} 시그널 - 가격: ${price:.4f}, 이유: {reason}"
        self._send_notification("SIGNAL", message)
    
    def send_error_notification(self, error: str):
        """에러 알림"""
        message = f"[{self.symbol}] 오류 발생: {error}"
        self._send_notification("ERROR", message)
    
    def send_status_notification(self, portfolio_status: Dict, current_price: float):
        """포트폴리오 상태 알림"""
        message = self._format_status_message(portfolio_status, current_price)
        self._send_notification("STATUS", message)
    
    def _format_trade_message(self, order: Dict, portfolio_status: Dict) -> str:
        """거래 메시지 포맷팅"""
        order_type = order.get("type", "unknown")
        quantity = order.get("quantity", 0)
        price = order.get("price", 0)
        
        message = f"[{self.symbol}] {order_type.upper()} 거래 완료\n"
        message += f"수량: {quantity:.6f}\n"
        message += f"가격: ${price:.4f}\n"
        
        if portfolio_status:
            holdings = portfolio_status.get("holdings", 0)
            avg_price = portfolio_status.get("avg_price", 0)
            profit_rate = portfolio_status.get("profit_rate", 0)
            
            message += f"보유량: {holdings:.6f}\n"
            message += f"평균단가: ${avg_price:.4f}\n"
            message += f"수익률: {profit_rate:.2f}%"
        
        return message
    
    def _format_status_message(self, portfolio_status: Dict, current_price: float) -> str:
        """상태 메시지 포맷팅"""
        holdings = portfolio_status.get("holdings", 0)
        avg_price = portfolio_status.get("avg_price", 0)
        profit = portfolio_status.get("profit", 0)
        profit_rate = portfolio_status.get("profit_rate", 0)
        
        message = f"[{self.symbol}] 포트폴리오 현황\n"
        message += f"현재가: ${current_price:.4f}\n"
        message += f"보유량: {holdings:.6f}\n"
        message += f"평균단가: ${avg_price:.4f}\n"
        message += f"손익: ${profit:.2f} ({profit_rate:.2f}%)"
        
        return message
    
    def _send_notification(self, notification_type: str, message: str):
        """알림 전송"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        
        notification = {
            "timestamp": timestamp,
            "type": notification_type,
            "symbol": self.symbol,
            "message": message
        }
        
        self.notification_history.append(notification)
        
        # 콘솔 출력
        if self.config.get("enable_console", True):
            print(f"[{timestamp}] {notification_type}: {message}")
        
        # 파일 로그
        if self.config.get("enable_file", True):
            self._write_to_file(notification)
        
        # 웹훅 전송
        if self.config.get("enable_webhook", False):
            self._send_webhook(notification)
    
    def _write_to_file(self, notification: Dict):
        """파일에 로그 작성"""
        try:
            import os
            log_file = self.config.get("log_file")
            
            # 로그 디렉토리 생성
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(notification, ensure_ascii=False) + "\n")
                
        except Exception as e:
            logger.error(f"[{self.symbol}] 파일 로그 작성 실패: {e}")
    
    def _send_webhook(self, notification: Dict):
        """웹훅으로 알림 전송"""
        try:
            import requests
            webhook_url = self.config.get("webhook_url")
            
            if webhook_url:
                response = requests.post(webhook_url, json=notification, timeout=5)
                response.raise_for_status()
                logger.info(f"[{self.symbol}] 웹훅 전송 완료")
                
        except Exception as e:
            logger.error(f"[{self.symbol}] 웹훅 전송 실패: {e}")
    
    def get_recent_notifications(self, count: int = 10) -> list:
        """최근 알림 내역 반환"""
        return self.notification_history[-count:] if self.notification_history else [] 