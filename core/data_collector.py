import time
import requests
from typing import Dict, Optional, List
from utils.logger import get_logger
from core.config import config

logger = get_logger(__name__)

class DataCollector:
    """업비트 전용 가격 데이터 수집기"""
    
    def __init__(self):
        self.price_cache = {}
        self.last_update = {}
        self.market_mapping = config.get_market_mapping()
        logger.info("업비트 데이터 수집기 초기화 완료")
    
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
            upbit_market = self.market_mapping.get(symbol)
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

    def _get_upbit_prices(self, symbols: List[str]) -> Dict[str, Optional[float]]:
        """여러 심볼의 가격을 한번에 조회"""
        results: Dict[str, Optional[float]] = {}
        try:
            symbol_to_market = {}
            markets = []
            for symbol in symbols:
                market = self.market_mapping.get(symbol)
                if not market:
                    logger.warning(f"[{symbol}] 업비트 마켓 매핑 없음")
                    results[symbol] = None
                    continue
                symbol_to_market[market] = symbol
                markets.append(market)

            if not markets:
                return results

            url = "https://api.upbit.com/v1/ticker"
            params = {"markets": ",".join(markets)}
            logger.debug(f"업비트 배치 가격 조회: {params['markets']}")

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            for item in data:
                market = item.get("market")
                price = float(item.get("trade_price")) if item.get("trade_price") is not None else None
                symbol = symbol_to_market.get(market)
                if symbol:
                    results[symbol] = price

            # 반환되지 않은 심볼은 None 처리
            for symbol in symbols:
                results.setdefault(symbol, None)

        except Exception as e:
            logger.error(f"배치 가격 조회 실패: {e}")
            for symbol in symbols:
                results.setdefault(symbol, None)

        return results
    
    def get_multiple_prices(self, symbols: list) -> Dict[str, Optional[float]]:
        """여러 심볼의 가격을 동시에 조회"""
        prices: Dict[str, Optional[float]] = {}
        fetch_symbols: List[str] = []

        # 캐시 확인
        for symbol in symbols:
            if (
                symbol in self.price_cache
                and symbol in self.last_update
                and time.time() - self.last_update[symbol] < 5
            ):
                prices[symbol] = self.price_cache[symbol]
            else:
                fetch_symbols.append(symbol)

        if fetch_symbols:
            fetched = self._get_upbit_prices(fetch_symbols)
            logger.debug(
                f"배치 조회 사용: {', '.join(fetch_symbols)}"
            )
            for sym, price in fetched.items():
                if price is not None:
                    self.price_cache[sym] = price
                    self.last_update[sym] = time.time()
                prices[sym] = price

        return prices
    
    def get_market_info(self, symbol: str) -> Optional[Dict]:
        """업비트 마켓 정보 조회"""
        try:
            upbit_market = self.market_mapping.get(symbol)
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