import re

with open('core/trader_loop.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Insert kis_sim and bithumb_sim right after kis_mock initialization
target = "self.kis_mock = KISClient(kis_url_v, kis_key_v, kis_sec_v, kis_cano_v, kis_acnt_v)"
replacement = target + """
            self.kis_sim = KISClient("http://127.0.0.1:8080", "mock", "mock", "mock", "01")
            
        try:
            self.bithumb_sim = BithumbClient("mock", "mock", "http://127.0.0.1:8080")
        except:
            pass # just in case BithumbClient signature was not patched correctly
"""
content = content.replace(target, replacement)

with open('core/trader_loop.py', 'w', encoding='utf-8') as f:
    f.write(content)
