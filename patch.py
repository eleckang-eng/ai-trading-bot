import sys
import re

with open('core/trader_loop.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add kis_sim and bithumb_sim
init_kis_code = '''
        if kis_key_v:
            self.kis_mock = KISClient(kis_url_v, kis_key_v, kis_sec_v, kis_cano_v, kis_acnt_v)
'''
new_init_kis_code = init_kis_code + '''
        self.kis_sim = KISClient("http://127.0.0.1:8080", "mock", "mock", "mock", "01")
        
        # Bithumb sim URL would be patched inside bithumb_api or we just add a hack for now.
        # But BithumbClient hardcodes URL. Let's patch bithumb_api later or pass url.
'''
content = content.replace(init_kis_code, new_init_kis_code)

kis_prop = '''
    @property
    def kis(self):
        return self.kis_mock if self.config.get("mock_mode", True) else self.kis_real
'''
new_kis_prop = '''
    @property
    def kis(self):
        if self.config.get("paper_trading", False):
            return self.kis_sim
        return self.kis_mock if self.config.get("mock_mode", True) else self.kis_real
'''
content = content.replace(kis_prop, new_kis_prop)

# 3. Add config table to _init_db
db_init = "CREATE TABLE IF NOT EXISTS trade_history"
new_db_init = """CREATE TABLE IF NOT EXISTS config (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS trade_history"""
content = content.replace(db_init, new_db_init)

# 4. Load config from DB in _init_db
load_cfg = '''
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
'''
new_load_cfg = load_cfg + '''
            import json
            cursor.execute("SELECT key, value FROM config")
            for row in cursor.fetchall():
                try:
                    self.config[row[0]] = json.loads(row[1])
                except:
                    self.config[row[0]] = row[1]
'''
content = content.replace(load_cfg, new_load_cfg)

# 5. Save config in update_config
upd_cfg = '''
    def update_config(self, config_updates):
        for k, v in config_updates.items():
            if isinstance(v, dict) and k in self.config and isinstance(self.config[k], dict):
                self.config[k].update(v)
            else:
                self.config[k] = v
        return self.config
'''
new_upd_cfg = '''
    def update_config(self, config_updates):
        for k, v in config_updates.items():
            if isinstance(v, dict) and k in self.config and isinstance(self.config[k], dict):
                self.config[k].update(v)
            else:
                self.config[k] = v
        
        import sqlite3, json
        with sqlite3.connect(self.db_path) as conn:
            for k, v in self.config.items():
                val_str = json.dumps(v)
                conn.execute("INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)", (k, val_str))
                
        return self.config
'''
content = content.replace(upd_cfg, new_upd_cfg)

bypass_code = '''
        # ── 테스트(paper_trading) 모드: 실제 API 전송 없이 DB만 기록 ────
        if self.config.get("paper_trading", False):
            self.save_position(symbol, quantity, price or 0, side=side)  # 매수/매도 모두 기록
            logger.info(f"[테스트-미전송] {order_type} {quantity}개 @ {price_str} DB 기록 완료")
            return {"status": "success", "message": f"[테스트 모드] {order_type} {quantity}주 @ {price_str} — 거래소 미전송, DB 기록 완료"}
'''
content = content.replace(bypass_code, "")

with open('core/trader_loop.py', 'w', encoding='utf-8') as f:
    f.write(content)
