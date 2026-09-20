import codecs
import re

file_path = r'd:\aiworkspace\exchanges\kis_api.py'
with codecs.open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

new_func = '''    def _place_order(self, symbol: str, price: int, quantity: int, is_buy: bool):
        import time
        path = "/uapi/domestic-stock/v1/trading/order-cash"
        url = f"{self.url_base}{path}"
        tr_id = "TTTC0802U" if is_buy else "TTTC0801U"
        headers = self._get_headers(tr_id)
        body = {
            "CANO": self.cano,
            "ACNT_PRDT_CD": self.acnt_prdt_cd,
            "PDNO": symbol,
            "ORD_DVSN": "00", # 00: 지정가
            "ORD_QTY": str(quantity),
            "ORD_UNPR": str(price),
        }
        
        max_retries = 5
        for attempt in range(max_retries):
            res = requests.post(url, headers=headers, data=json.dumps(body))
            data = res.json()
            
            rt_cd = str(data.get("rt_cd", "0"))
            msg1 = data.get("msg1", "")
            msg_cd = data.get("msg_cd", "")
            
            # KIS Rate Limit 에러 방어적 프로그래밍 (초당 거래건수 초과 등)
            if rt_cd != "0" and ("초과" in msg1 or "건수" in msg1 or "EGW00" in msg_cd):
                print(f"[Rate Limit] KIS API 제한 도달 ({msg1}). 1초 대기 후 재시도... ({attempt+1}/{max_retries})")
                time.sleep(1.2)
                continue
                
            return data
            
        return res.json()'''

content = re.sub(r'    def _place_order\(self, symbol: str, price: int, quantity: int, is_buy: bool\):[\s\S]*?return res\.json\(\)', new_func, content)

with codecs.open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Patch applied to kis_api.py!')

