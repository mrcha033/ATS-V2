import jwt
import uuid
import hashlib
import requests
import time
from urllib.parse import urlencode
from typing import Dict, List, Optional
from utils.logger import get_logger
from core.config import config

logger = get_logger(__name__)

class UpbitClient:
    """업비트 API 클라이언트"""
    
    def __init__(self, access_key: str = None, secret_key: str = None):
        # 환경변수에서 API 키 가져오기
        self.access_key = access_key or config.upbit_access_key
        self.secret_key = secret_key or config.upbit_secret_key
        
        if not self.access_key or not self.secret_key:
            raise ValueError("업비트 API 키가 설정되지 않았습니다. .env 파일을 확인하세요.")
        
        self.base_url = "https://api.upbit.com"
        self.session = requests.Session()
        logger.info("업비트 클라이언트 초기화 완료")
    
    def _generate_jwt_token(self, query_params: Dict = None) -> str:
        """JWT 토큰 생성"""
        payload = {
            'access_key': self.access_key,
            'nonce': str(uuid.uuid4()),
        }
        
        # 파라미터가 있는 경우 query_hash 생성
        if query_params:
            query_string = urlencode(query_params)
            m = hashlib.sha512()
            m.update(query_string.encode())
            query_hash = m.hexdigest()
            
            payload.update({
                'query_hash': query_hash,
                'query_hash_alg': 'SHA512'
            })
        
        jwt_token = jwt.encode(payload, self.secret_key, algorithm='HS256')
        return f"Bearer {jwt_token}"
    
    def get_ticker(self, market: str) -> Optional[Dict]:
        """현재가 조회"""
        try:
            url = f"{self.base_url}/v1/ticker"
            params = {'markets': market}
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            if data and len(data) > 0:
                return data[0]
            return None
            
        except Exception as e:
            logger.error(f"업비트 현재가 조회 실패 [{market}]: {e}")
            return None
    
    def get_accounts(self) -> List[Dict]:
        """계좌 정보 조회"""
        try:
            url = f"{self.base_url}/v1/accounts"
            headers = {'Authorization': self._generate_jwt_token()}
            
            response = self.session.get(url, headers=headers)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"업비트 계좌 조회 실패: {e}")
            return []
    
    def place_order(self, market: str, side: str, ord_type: str, 
                   volume: float = None, price: float = None) -> Optional[Dict]:
        """주문 실행"""
        try:
            url = f"{self.base_url}/v1/orders"
            
            params = {
                'market': market,
                'side': side,  # 'bid' (매수) or 'ask' (매도)
                'ord_type': ord_type,  # 'limit' or 'market'
            }
            
            if volume:
                params['volume'] = str(volume)
            if price:
                params['price'] = str(int(price))
            
            headers = {
                'Authorization': self._generate_jwt_token(params),
                'Content-Type': 'application/json; charset=utf-8'
            }
            
            response = self.session.post(url, json=params, headers=headers)
            response.raise_for_status()
            
            order_result = response.json()
            logger.info(f"업비트 주문 성공 [{market}]: {side} {volume} @ {price}")
            return order_result
            
        except Exception as e:
            logger.error(f"업비트 주문 실패 [{market}]: {e}")
            return None
    
    def cancel_order(self, uuid_or_identifier: str) -> Optional[Dict]:
        """주문 취소"""
        try:
            url = f"{self.base_url}/v1/order"
            params = {'uuid': uuid_or_identifier}
            
            headers = {'Authorization': self._generate_jwt_token(params)}
            
            response = self.session.delete(url, params=params, headers=headers)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"업비트 주문 취소 실패: {e}")
            return None
    
    def get_orders(self, market: str = None, state: str = 'wait') -> List[Dict]:
        """주문 목록 조회"""
        try:
            url = f"{self.base_url}/v1/orders"
            params = {'state': state}
            
            if market:
                params['market'] = market
            
            headers = {'Authorization': self._generate_jwt_token(params)}
            
            response = self.session.get(url, params=params, headers=headers)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"업비트 주문 목록 조회 실패: {e}")
            return [] 