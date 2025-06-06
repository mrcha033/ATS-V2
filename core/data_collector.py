import time
import requests
import json
from typing import Dict, Optional
from utils.logger import get_logger

logger = get_logger(__name__)

class DataCollector:
    """업비트 전용 가격 데이터 수집기"""
    
    def __init__(self):
        self.price_cache = {}
        self.last_update = {}
        self._load_upbit_config()
    
    def _load_upbit_config(self):
        """업비트 설정 로드"""
        try:
            with open('config/upbit_config.json', 'r', encoding='utf-8') as f:
                self.upbit_config = json.load(f)
            logger.info("업비트 설정 로드 완료")
        except Exception as e:
            logger.error(f"업비트 설정 로드 실패: {e}")
            self.upbit_config = {}
    
    def get_price(self, symbol: str) -> Optional[float]:
        """업비트에서 현재 가격 조회"""
        try:
            # 캐시된 가격이 5초 이내인 경우 캐시 사용
            if (symbol in self.price_cache and 
                symbol in self.last_update and 
                time.time() - self.last_update[symbol] < 5):
                return self.price_cache[symbol]
            
            price = self._get_upbit_price(symbol)
            
            if price:
                # 캐시 업데이트
                self.price_cache[symbol] = price
                self.last_update[symbol] = time.time()
                logger.debug(f"[{symbol}] 가격 조회: {price:,.0f} KRW")
            
            return price
            
        except Exception as e:
            logger.error(f"[{symbol}] 가격 조회 실패: {e}")
            return None
    
    def _get_upbit_price(self, symbol: str) -> Optional[float]:
        """업비트에서 가격 조회"""
        try:
            # 심볼을 업비트 마켓으로 매핑
            upbit_market = self.upbit_config.get('market_mapping', {}).get(symbol)
            if not upbit_market:
                logger.warning(f"[{symbol}] 업비트 마켓 매핑 없음")
                return None
            
            # 업비트 공개 API로 현재가 조회
            url = "https://api.upbit.com/v1/ticker"
            params = {'markets': upbit_market}
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data and len(data) > 0:
                price = float(data[0]['trade_price'])
                return price
            
            return None
            
        except Exception as e:
            logger.error(f"[{symbol}] 업비트 가격 조회 실패: {e}")
            return None
    
    def get_multiple_prices(self, symbols: list) -> Dict[str, Optional[float]]:
        """여러 심볼의 가격을 동시에 조회"""
        prices = {}
        for symbol in symbols:
            prices[symbol] = self.get_price(symbol)
        return prices
    
    def get_market_info(self, symbol: str) -> Optional[Dict]:
        """업비트 마켓 정보 조회"""
        try:
            upbit_market = self.upbit_config.get('market_mapping', {}).get(symbol)
            if not upbit_market:
                return None
            
            url = "https://api.upbit.com/v1/market/all"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            markets = response.json()
            for market in markets:
                if market['market'] == upbit_market:
                    return market
            
            return None
            
        except Exception as e:
            logger.error(f"[{symbol}] 마켓 정보 조회 실패: {e}")
            return None 