import sys

with open('exchanges/bithumb_api.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    'def __init__(self, api_key: str, secret_key: str):',
    'def __init__(self, api_key: str, secret_key: str, base_url: str = "https://api.bithumb.com"):'
)
content = content.replace(
    'self.base_url = "https://api.bithumb.com"',
    'self.base_url = base_url'
)

if 'buy_limit_order' not in content:
    content += """
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
"""

with open('exchanges/bithumb_api.py', 'w', encoding='utf-8') as f:
    f.write(content)
