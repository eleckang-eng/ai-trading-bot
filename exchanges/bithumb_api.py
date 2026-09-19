import requests
import jwt
import uuid
import time
import logging
from .base import BaseExchange

logger = logging.getLogger("BithumbAPI")

class BithumbClient(BaseExchange):
    def __init__(self, api_key: str, secret_key: str, base_url: str = "https://api.bithumb.com"):
        self.api_key = api_key
        self.secret_key = secret_key
        self.base_url = base_url

    def _get_headers(self, query_hash=None):
        payload = {
            'access_key': self.api_key,
            'nonce': str(uuid.uuid4()),
            'timestamp': round(time.time() * 1000)
        }
        if query_hash:
            payload['query_hash'] = query_hash
            payload['query_hash_alg'] = 'SHA512'

        jwt_token = jwt.encode(payload, self.secret_key, algorithm='HS256')
        return {'Authorization': f'Bearer {jwt_token}'}

    def get_balance(self):
        """
        API 2.0 (v1/accounts) 기반 계좌 잔고 조회
        반환값: (원화잔고 등)
        """
        try:
            url = f"{self.base_url}/v1/accounts"
            headers = self._get_headers()
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                # Upbit 형식과 유사 [{currency: 'KRW', balance: '1000', locked: '0'}, ...]
                accounts = response.json()
                krw_balance = 0
                for acc in accounts:
                    if acc['currency'] == 'KRW':
                        krw_balance = float(acc['balance'])
                # TraderLoop 호환성을 위해 [0, 0, krw_balance, 0] 형태로 반환
                return (0, 0, krw_balance, 0)
            else:
                logger.error(f"Bithumb get_balance error: {response.text}")
                return None
        except Exception as e:
            logger.error(f"Bithumb get_balance exception: {e}")
            return None

    def get_current_price(self, symbol: str):
        """
        현재가 조회
        symbol: "ONDO" 등
        """
        try:
            # v1 ticker 사용
            url = f"{self.base_url}/public/ticker/{symbol}_KRW"
            res = requests.get(url)
            if res.status_code == 200:
                data = res.json()
                if data.get('status') == '0000':
                    return float(data['data']['closing_price'])
            return None
        except Exception as e:
            logger.error(f"Bithumb get_current_price error: {e}")
            return None

    def buy_limit(self, symbol: str, price: int, quantity: float):
        # TODO: API 2.0 주문 로직 구현 필요
        pass

    def sell_limit(self, symbol: str, price: int, quantity: float):
        # TODO: API 2.0 주문 로직 구현 필요
        pass

    def cancel_order(self, order_id: tuple):
        pass

    def buy_limit_order(self, symbol: str, price: float, quantity: float):
        url = f"{self.base_url}/trade/place"
        import requests
        return requests.post(url, data={"order_currency": symbol, "payment_currency": "KRW", "units": quantity, "price": price, "type": "bid"}).json()
        
    def sell_limit_order(self, symbol: str, price: float, quantity: float):
        url = f"{self.base_url}/trade/place"
        import requests
        return requests.post(url, data={"order_currency": symbol, "payment_currency": "KRW", "units": quantity, "price": price, "type": "ask"}).json()
        
    def get_open_orders(self, symbol: str):
        return {"status": "0000", "data": []}
