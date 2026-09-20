import sys

with open('core/trader_loop.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the previous mock_kis init with bithumb_sim
init_kis_code = 'self.kis_sim = KISClient("http://127.0.0.1:8080", "mock", "mock", "mock", "01")'
if 'self.bithumb_sim' not in content:
    content = content.replace(
        init_kis_code,
        init_kis_code + '\\n        self.bithumb_sim = BithumbClient("mock", "mock", "http://127.0.0.1:8080")'
    )

bithumb_prop = '''
    @property
    def bithumb(self):
        return self.bithumb_client
'''
new_bithumb_prop = '''
    @property
    def bithumb(self):
        if self.config.get("paper_trading", False):
            return self.bithumb_sim
        return self.bithumb_client
'''
content = content.replace(bithumb_prop, new_bithumb_prop)

with open('core/trader_loop.py', 'w', encoding='utf-8') as f:
    f.write(content)
