import re

with open('core/trader_loop.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = re.sub(
    r'def kis\(self\):.*?return self\.kis_mock if self\.config\.get\("mock_mode", True\) else self\.kis_real',
    '''def kis(self):
        if self.config.get("paper_trading", False):
            return self.kis_sim
        return self.kis_mock if self.config.get("mock_mode", True) else self.kis_real''',
    content, flags=re.DOTALL
)

with open('core/trader_loop.py', 'w', encoding='utf-8') as f:
    f.write(content)
