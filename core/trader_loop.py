import asyncio
import sqlite3
import os
import logging
from dotenv import load_dotenv
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from exchanges.kis_api import KISClient
from exchanges.bithumb_api import BithumbClient

# Set up logging
log_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'app.log')
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file_path, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("TraderLoop")

load_dotenv()

class TraderLoop:
    def __init__(self):
        self.running = False
        self.balances = {"kis": 0, "bithumb": 0}  # 거래소별 잔고 캐시
        default_ex = os.getenv("DEFAULT_EXCHANGE", "kis")
        default_mock = os.getenv("MOCK_MODE", "false").lower() in ("true", "1", "yes")
        default_sym = "042660" if default_ex == "kis" else "ONDO"
        self.config = {
            "symbol": default_sym, 
            "exchange": default_ex,
            "mock_mode": default_mock,
            "bithumb": {
                "grid_interval": 10,
                "take_profit": 10,
                "order_quantity": 1000
            },
            "kis": {
                "grid_interval": 2000,
                "take_profit": 2000,
                "order_quantity": 10
            }
        }
        # DB setup
        self.db_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
        os.makedirs(self.db_dir, exist_ok=True)
        self.db_path = os.path.join(self.db_dir, 'positions.db')
        self._init_db()
        
        # KIS 실전 Setup
        kis_url = os.getenv("KIS_URL_BASE", "")
        kis_key = os.getenv("KIS_APP_KEY", "")
        kis_sec = os.getenv("KIS_APP_SECRET", "")
        kis_cano = os.getenv("KIS_CANO", "")
        kis_acnt = os.getenv("KIS_ACNT_PRDT_CD", "01")
        
        # KIS 모의 Setup
        kis_url_v = os.getenv("KIS_URL_BASE_MOCK_V", "https://openapivts.koreainvestment.com:29443")
        kis_key_v = os.getenv("KIS_APP_KEY_MOCK_V", "")
        kis_sec_v = os.getenv("KIS_APP_SECRET_MOCK_V", "")
        kis_cano_v = os.getenv("KIS_CANO_V", "")
        kis_acnt_v = os.getenv("KIS_ACNT_PRDT_CD_V", "01")
        
        # Bithumb Setup
        self.bithumb_key = os.getenv("BITHUMB_API_KEY", "")
        self.bithumb_secret = os.getenv("BITHUMB_SECRET_KEY", "")

        self.loop_task = None
        
        self.kis_real = None
        self.kis_mock = None
        
        try:
            if kis_key:
                self.kis_real = KISClient(kis_url, kis_key, kis_sec, kis_cano, kis_acnt)
        except Exception as e:
            logger.error(f"Failed to initialize KIS Real: {e}")
            
        try:
            if kis_key_v:
                self.kis_mock = KISClient(kis_url_v, kis_key_v, kis_sec_v, kis_cano_v, kis_acnt_v)
                
            self.kis_sim = KISClient("http://127.0.0.1:8080", "mock", "mock", "mock", "01")
            self.bithumb_sim = BithumbClient("mock", "mock", "http://127.0.0.1:8080")
        except Exception as e:
            logger.error(f"KIS/Bithumb init error: {e}")
            
        try:
            if self.bithumb_key and self.bithumb_secret:
                self.bithumb = BithumbClient(self.bithumb_key, self.bithumb_secret)
            else:
                self.bithumb = None
        except Exception as e:
            logger.error(f"Failed to initialize Bithumb Client: {e}")
            self.bithumb = None

    @property
    def kis(self):
        """mock_mode 여부에 따라 진짜/모의 클라이언트를 동적 반환"""
        if self.config.get("paper_trading", False):
            return self.kis_sim
        return self.kis_mock if self.config.get("mock_mode", True) else self.kis_real

    def _get_mode_key(self):
        """현재 거래소/모드 조합 키 반환 (모드별 DB 분리용)"""
        ex = self.config.get("exchange", "kis")
        if self.config.get("paper_trading", False):
            return f"{ex}_test"
        elif self.config.get("mock_mode", True):
            return f"{ex}_mock"
        else:
            return f"{ex}_real"

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS grid_bullets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT,
                    quantity REAL,
                    buy_price REAL,
                    side TEXT DEFAULT 'buy',
                    exchange_mode TEXT DEFAULT 'kis_mock'
                )
            ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS config (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS trade_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT,
                    quantity REAL,
                    price REAL,
                    side TEXT,
                    exchange_mode TEXT,
                    filled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'filled'
                )
            ''')
            # 기존 테이블 마이그레이션: side, exchange_mode, order_id 컬럼 추가
            for col, default in [("side", "'buy'"), ("exchange_mode", "'kis_mock'"), ("order_id", "''")]:
                try:
                    conn.execute(f"ALTER TABLE grid_bullets ADD COLUMN {col} TEXT DEFAULT {default}")
                except Exception:
                    pass
            conn.commit()

    def record_trade(self, symbol, quantity, price, side, exchange_mode, status="filled"):
        """체결된 내역을 trade_history에 기록"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO trade_history (symbol, quantity, price, side, exchange_mode, status)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (symbol, quantity, price, side, exchange_mode, status))
            conn.commit()

    def get_history(self, limit=50):
        mode_key = self._get_mode_key()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT filled_at, side, price, quantity, status 
                FROM trade_history 
                WHERE exchange_mode = ? 
                ORDER BY id DESC LIMIT ?
            ''', (mode_key, limit))
            rows = cursor.fetchall()
            return [{'filled_at': r[0], 'side': r[1], 'price': r[2], 'quantity': r[3], 'status': r[4]} for r in rows]

    def clear_history(self):
        """현재 모드의 거래내역 영구 삭제"""
        mode_key = self._get_mode_key()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('DELETE FROM trade_history WHERE exchange_mode = ?', (mode_key,))
            conn.commit()
        return {"status": "success", "message": f"{mode_key} 거래 내역이 초기화되었습니다."}

    def _calculate_profit_and_count(self):
        mode_key = self._get_mode_key()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT filled_at, side, price, quantity 
                FROM trade_history 
                WHERE exchange_mode = ? AND status = 'filled'
                ORDER BY id ASC
            ''', (mode_key,))
            rows = cursor.fetchall()
            
        import datetime
        today_str = datetime.datetime.now().strftime("%Y-%m-%d")
        
        unmatched_buys = []
        total_profit = 0.0
        today_trade_count = 0
        
        # 기본 DB 기반 명목 수익 및 체결 횟수 산출 (FIFO)
        for row in rows:
            filled_at_str, side, price, qty = row
            
            if filled_at_str.startswith(today_str):
                today_trade_count += 1
                
            if side == 'buy':
                unmatched_buys.append({"price": float(price), "qty": float(qty)})
            elif side == 'sell':
                sell_qty = float(qty)
                sell_price = float(price)
                
                while sell_qty > 0 and unmatched_buys:
                    oldest_buy = unmatched_buys[0]
                    match_qty = min(sell_qty, oldest_buy["qty"])
                    
                    # FIFO 기반 차익 산출
                    gross_profit = (sell_price - oldest_buy["price"]) * match_qty
                    
                    # 수수료(Fee) 및 세금(Tax) 자체 캘리브레이션 (Bithumb 0.04%, KIS 0.2% 매도세율 가정)
                    fee_rate = 0.00215 if "kis" in mode_key else 0.0004
                    net_profit = gross_profit - (sell_price * match_qty * fee_rate)
                    
                    total_profit += net_profit
                    
                    sell_qty -= match_qty
                    oldest_buy["qty"] -= match_qty
                    
                    if oldest_buy["qty"] <= 0:
                        unmatched_buys.pop(0)

        # KIS 실거래 모드인 경우 하이브리드 오차 보정 (거래소 API 호출)
        if mode_key == "kis_real" and self.kis:
            # 1분 단위 캐싱을 통해 무분별한 API 호출(Rate Limit) 방지
            import time
            current_time = time.time()
            if current_time - getattr(self, "_last_profit_sync", 0) > 60:
                self._last_profit_sync = current_time
                try:
                    start_dt = datetime.datetime.now().strftime("%Y%m01") # 당월 1일부터 조회
                    end_dt = datetime.datetime.now().strftime("%Y%m%d")
                    res = self.kis.get_realized_profit(start_dt, end_dt)
                    if res.get("rt_cd") == "0":
                        out2 = res.get("output2", [])
                        if out2 and isinstance(out2, list):
                            # API에서 실현손익을 제공하면 그 값으로 덮어씀 (안전한 보정)
                            # 보통 rlzt_pfls_amt 또는 tot_rlzt_pfls_amt 키 사용
                            calibrated_profit = float(out2[0].get("rlzt_pfls_amt", out2[0].get("tot_rlzt_pfls_amt", total_profit)))
                            total_profit = calibrated_profit
                except Exception as e:
                    # self.logger가 아닌 모듈 레벨 logger 사용 (TraderLoop에 logger 인스턴스 속성 없음)
                    logger.error(f"실현손익 API 캘리브레이션 실패: {e}")

        return total_profit, today_trade_count

    def get_positions(self):
        mode_key = self._get_mode_key()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            import json
            cursor.execute("SELECT key, value FROM config")
            for row in cursor.fetchall():
                try:
                    self.config[row[0]] = json.loads(row[1])
                except:
                    self.config[row[0]] = row[1]
            cursor.execute(
                "SELECT id, symbol, quantity, buy_price, side, order_id FROM grid_bullets WHERE exchange_mode = ?",
                (mode_key,)
            )
            rows = cursor.fetchall()
            return [{"id": r[0], "symbol": r[1], "quantity": r[2], "avg_price": r[3], "side": r[4] or "buy", "order_id": r[5] or ""} for r in rows]

    def save_position(self, symbol, quantity, buy_price, side="buy", order_id=""):
        mode_key = self._get_mode_key()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO grid_bullets (symbol, quantity, buy_price, side, exchange_mode, order_id)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (symbol, quantity, buy_price, side, mode_key, order_id))
            conn.commit()

    def _cancel_order_via_api(self, exchange_mode, order_id, symbol):
        if not order_id: return True # 테스트용 데이터거나 uuid 없는 경우 그냥 지움
        exchange = exchange_mode.split("_")[0]
        try:
            if exchange == "kis" and self.kis:
                res = self.kis.cancel_order(order_id, symbol)
                if isinstance(res, dict) and res.get("rt_cd") != "0":
                    raise Exception(f"KIS Cancel Error: {res}")
            elif exchange == "bithumb" and self.bithumb:
                res = self.bithumb.cancel_order(order_id, symbol)
                if isinstance(res, dict) and "uuid" not in res:
                    # 빗썸 취소 실패 시 에러
                    if res.get("error"):
                        raise Exception(f"Bithumb Cancel Error: {res}")
        except Exception as e:
            logger.error(f"API Cancel Failed for {order_id}: {e}")
            raise e
        return True

    def delete_position(self, position_id, cancel_api=True, force=False):
        """개별 포지션 취소 및 삭제
        - cancel_api=True: 증권사 취소 API를 먼저 호출
        - force=True: API 취소 실패 여부와 관계없이 DB에서 강제 삭제 (장 외 시간 정리용)
        - force=False (기본): API 취소 실패 시 DB 삭제 보류 (증권사에 주문이 살아있을 수 있으므로)"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT exchange_mode, order_id, symbol, quantity, buy_price, side FROM grid_bullets WHERE id = ?', (position_id,))
            row = cursor.fetchone()
            if row:
                ex_mode, order_id, symbol, qty, price, side = row
                if cancel_api and order_id:
                    try:
                        self._cancel_order_via_api(ex_mode, order_id, symbol)
                        self.record_trade(symbol, qty, price, side, ex_mode, "canceled")
                    except Exception as e:
                        logger.error(f"API 취소 실패 (ID: {position_id}, ODNO: {order_id}): {e}")
                        if not force:
                            # 증권사에 주문이 살아있을 수 있으므로 DB 삭제 보류
                            return False
                        # force=True: 사용자가 명시적으로 강제 삭제를 요청한 경우
                        logger.warning(f"강제 삭제 모드: DB에서 제거합니다 (ID: {position_id})")
                        self.record_trade(symbol, qty, price, side, ex_mode, "force_canceled")
                else:
                    self.record_trade(symbol, qty, price, side, ex_mode, "canceled")
            conn.execute('DELETE FROM grid_bullets WHERE id = ?', (position_id,))
            conn.commit()
        return True

    def delete_all_positions(self, force=False):
        """현재 모드의 포지션 일괄 취소 및 삭제
        - force=False (기본): API 취소 성공한 것만 DB에서 삭제, 실패한 것은 보류
        - force=True: API 실패 여부와 관계없이 전부 DB에서 삭제"""
        import time
        mode_key = self._get_mode_key()
        success_count = 0
        fail_count = 0
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, order_id, symbol, quantity, buy_price, side FROM grid_bullets WHERE exchange_mode = ?', (mode_key,))
            rows = cursor.fetchall()
            for r in rows:
                p_id, o_id, sym, qty, price, side = r
                api_ok = False
                if o_id:
                    try:
                        self._cancel_order_via_api(mode_key, o_id, sym)
                        api_ok = True
                        success_count += 1
                    except Exception as e:
                        fail_count += 1
                        logger.error(f"API 취소 실패 (ODNO: {o_id}): {e}")
                    time.sleep(0.3)
                else:
                    api_ok = True
                    success_count += 1
                
                if api_ok:
                    self.record_trade(sym, qty, price, side, mode_key, "canceled")
                    conn.execute('DELETE FROM grid_bullets WHERE id = ?', (p_id,))
                elif force:
                    self.record_trade(sym, qty, price, side, mode_key, "force_canceled")
                    conn.execute('DELETE FROM grid_bullets WHERE id = ?', (p_id,))
                    logger.warning(f"강제 삭제: ODNO {o_id} (ID: {p_id})")
                # else: DB 삭제 보류 (증권사에 주문이 살아있을 수 있음)
            conn.commit()
        return success_count, fail_count


    def update_balance(self):
        exchange = self.config.get("exchange", "kis")
        self.balances[exchange] = 0  # 초기화
        success = False
        
        if exchange == "kis" and self.kis:
            try:
                bal_data = self.kis.get_balance()
                if isinstance(bal_data, dict) and bal_data.get('rt_cd') == '0':
                    self.balances["kis"] = int(bal_data['output2'][0]['dnca_tot_amt'])
                    success = True
                else:
                    logger.error(f"KIS Balance Error: {bal_data}")
            except Exception as e:
                logger.error(f"KIS Balance exception: {e}")
                
        elif exchange == "bithumb" and self.bithumb:
            try:
                bal_data = self.bithumb.get_balance()
                if bal_data:
                    self.balances["bithumb"] = int(bal_data[2])
                    success = True
            except Exception as e:
                logger.error(f"Bithumb Balance fetch error: {e}")
                
        if success:
            self._last_balance_update = __import__("time").time()
        return success

    def get_status(self):
        # 5초 초과 시 자동 잔고 갱신 (TTL 기반 실시간 보장)
        current_time = __import__("time").time()
        if current_time - getattr(self, "_last_balance_update", 0) > 5:
            self.update_balance()
            
        current_exchange = self.config.get("exchange", "kis")
        is_connected = False
        if current_exchange == "kis":
            is_connected = self.kis is not None
        elif current_exchange == "bithumb":
            is_connected = self.bithumb is not None
        bal = self.balances.get(current_exchange, 0)
        
        profit, trade_count = self._calculate_profit_and_count()

        return {
            "running": self.running,
            "config": self.config,
            "balance": bal,
            "positions": self.get_positions(),
            "exchange_connected": is_connected,
            "total_profit": int(profit),
            "trade_count": trade_count
        }

    def start(self):
        if not self.running:
            self.running = True
            # asyncio.create_task is used when running within an existing event loop (like FastAPI's)
            self.loop_task = asyncio.create_task(self.run_loop())
            logger.info("TraderLoop start requested.")
        return self.get_status()

    def stop(self):
        if self.running:
            self.running = False
            logger.info("TraderLoop stop requested.")
        return self.get_status()

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
            # 명시적 커밋: 예외 발생 시 롤백 방지 및 타 메서드와의 일관성 유지
            conn.commit()
            
        return self.config
        
    def manual_order(self, side, quantity, price=None):
        """수동 매수/매도 주문 (price가 None이면 시장가)"""
        order_type = "매수" if side == "buy" else "매도"
        price_str  = f"{price:,.0f}원 지정가" if price else "시장가"
        symbol     = self.config.get("symbol",   "042660")
        exchange   = self.config.get("exchange", "kis")

        mode_str = "모의투자" if self.config.get("mock_mode", True) else "실전투자"

        try:
            api_res = None
            if exchange == "kis" and self.kis:
                order_price = int(price) if price else 0
                order_qty   = int(quantity)
                if side == "buy":
                    api_res = self.kis.buy_limit(symbol, order_price, order_qty)
                else:
                    api_res = self.kis.sell_limit(symbol, order_price, order_qty)

            elif exchange == "bithumb" and self.bithumb:
                order_price = float(price) if price else 0
                order_qty   = float(quantity)
                if side == "buy":
                    api_res = self.bithumb.buy_limit_order(symbol, order_price, order_qty)
                else:
                    api_res = self.bithumb.sell_limit_order(symbol, order_price, order_qty)
            else:
                return {"status": "error", "message": f"{exchange} 거래소 연결이 되어있지 않습니다."}

            logger.info(f"[{mode_str}] 수동 {order_type} API 접수: {quantity}개 @ {price_str} / 응답: {api_res}")

            is_success = False
            msg = str(api_res)
            order_id = ""
            if exchange == "kis":
                if isinstance(api_res, dict) and api_res.get("rt_cd") == "0":
                    is_success = True
                    msg = api_res.get("msg1", "성공")
                    order_id = api_res.get("output", {}).get("ODNO", "")
            elif exchange == "bithumb":
                if isinstance(api_res, dict) and ("uuid" in api_res or api_res.get("status") == "0000"):
                    is_success = True
                    msg = "성공"
                    order_id = api_res.get("uuid", "")

            if is_success:
                self.save_position(symbol, quantity, price or 0, side=side, order_id=order_id)  # 매수/매도 모두 DB 기록
                return {"status": "success", "message": f"{order_type} 주문 체결 접수 성공: {msg}"}
            else:
                return {"status": "error", "message": f"주문 실패: {msg}"}
                
        except Exception as e:
            logger.error(f"Manual Order Error: {e}")
            return {"status": "error", "message": f"주문 실행 중 오류: {e}"}

    def cancel_all_orders(self):
        """현재 모드의 미체결 주문 일괄 취소 및 DB 초기화"""
        mode_key = self._get_mode_key()
        success_count, fail_count = self.delete_all_positions()
        logger.info(f"[{mode_key}] 포지션 및 미체결 주문 일괄 취소 (성공: {success_count}, API실패: {fail_count})")
        return {"status": "success", "message": f"{success_count}건 취소 완료 (API실패 {fail_count}건은 DB에서 강제 제거)", "success_count": success_count, "fail_count": fail_count}

    def _place_pingpong_order(self, exchange, symbol, filled_side, filled_price, qty, mode_key):
        """체결된 주문의 반대 방향으로 핑퐁 주문(그리드 간격 * 2)을 생성하고 틱 보정 규칙을 적용합니다."""
        ex_cfg = self.config.get(exchange, {})
        grid_interval = ex_cfg.get("grid_interval", 2000 if exchange == "kis" else 10)
        is_kis = exchange == "kis"
        
        # 핑퐁 타겟 가격 계산 (구간의 2배: * 2)
        pingpong_margin = grid_interval * 2
        
        target_price = 0
        side_to_place = "buy"
        
        if filled_side == "buy":
            # 매수 체결 -> 위로(*2) 매도 핑퐁
            target_price = float(filled_price) + pingpong_margin
            if is_kis:
                target_price = round((target_price - 900) / 1000) * 1000 + 900
            else:
                target_price = round((target_price - 9) / 10) * 10 + 9
            side_to_place = "sell"
            
        elif filled_side == "sell":
            # 매도 체결 -> 아래로(*2) 매수 핑퐁
            target_price = float(filled_price) - pingpong_margin
            if target_price <= 0:
                logger.warning(f"[핑퐁 오류] 계산된 매수 가격이 0 이하입니다: {target_price}")
                return
            if is_kis:
                target_price = round((target_price - 100) / 1000) * 1000 + 100
            else:
                target_price = round((target_price - 1) / 10) * 10 + 1
            side_to_place = "buy"

        logger.info(f"[{exchange} 핑퐁] {filled_side} 체결({filled_price}) 감지 -> {side_to_place} 핑퐁 주문({target_price}) 전송")
        
        # 실제 주문 및 DB 기록 (API Rate Limit 방어를 위해 1초 대기)
        import time
        time.sleep(1.0)
        self.manual_order(side_to_place, qty, target_price)

    def sync_orders(self):
        """실제 거래소의 미체결 내역 및 체결 내역을 이중 조회하여 DB와 동기화합니다."""
        mode_key = self._get_mode_key()
        
        # 테스트 모드는 시뮬레이터(run_loop)가 이미 처리하므로 스킵
        if self.config.get("paper_trading", False):
            return {"status": "success", "message": "테스트 모드는 내부 시뮬레이터로 자동 동기화됩니다."}
            
        exchange = self.config.get("exchange", "kis")
        try:
            if exchange == "kis" and self.kis:
                import datetime
                # 1. 미체결 주문 조회 (현재 살아있는 주문)
                open_res = self.kis.get_open_orders()
                # 2. 전일~당일 체결 내역 조회 (어제 체결된 것도 확인)
                today = datetime.datetime.now()
                yesterday = today - datetime.timedelta(days=1)
                today_str = today.strftime("%Y%m%d")
                yesterday_str = yesterday.strftime("%Y%m%d")
                filled_res = self.kis.get_daily_orders(yesterday_str, today_str)
                
                if open_res.get("rt_cd") == "0" and filled_res.get("rt_cd") == "0":
                    open_list = open_res.get("output", [])
                    filled_list = filled_res.get("output1", []) if "output1" in filled_res else filled_res.get("output", [])
                    
                    # 가격(p_price) 의존 탈피: 정확한 주문번호(odno) 기반으로 수동 주문과 100% 분리
                    open_odnos = {str(o.get("odno", "")).strip() for o in open_list}
                    filled_odnos = {str(o.get("odno", "")).strip() for o in filled_list}
                    filled_odnos.update({str(o.get("orgn_odno", "")).strip() for o in filled_list})
                    
                    db_positions = self.get_positions()
                    removed_count = 0
                    
                    # 빗썸과 동일하게 매수/매도 분리 후 현재가 기준 정렬
                    buys = sorted([p for p in db_positions if p['side'] == 'buy'], key=lambda x: float(x['avg_price']), reverse=True)
                    sells = sorted([p for p in db_positions if p['side'] == 'sell'], key=lambda x: float(x['avg_price']))

                    def _smart_sync_kis(sorted_pos, max_check=2):
                        nonlocal removed_count
                        unfilled_checked = 0
                        for pos in sorted_pos:
                            if unfilled_checked >= max_check:
                                break
                                
                            order_id = str(pos.get('order_id', "")).strip()
                            if not order_id:
                                continue
                                
                            # 미체결 리스트에 살아있는지 단건(주문번호)으로 확인
                            if order_id in open_odnos:
                                unfilled_checked += 1  # 아직 안 팔림 (wait)
                            else:
                                # 미체결에 없다면 처리(체결/취소)된 상태이므로 DB에서 정리하고 다음 호가로 확장
                                if order_id in filled_odnos:
                                    logger.info(f"[한투 동기화] 체결 확인됨 (ODNO: {order_id}) -> DB 이동 및 핑퐁 생성")
                                    self.record_trade(pos['symbol'], pos['quantity'], pos['avg_price'], pos['side'], mode_key, "filled")
                                    self.delete_position(pos['id'], cancel_api=False)
                                    removed_count += 1
                                    
                                    # 핑퐁(Ping-Pong) 반대 주문 발송
                                    self._place_pingpong_order("kis", pos['symbol'], pos['side'], pos['avg_price'], pos['quantity'], mode_key)
                                else:
                                    logger.info(f"[한투 동기화] 취소 확인됨 (ODNO: {order_id}) -> DB 이동")
                                    self.record_trade(pos['symbol'], pos['quantity'], pos['avg_price'], pos['side'], mode_key, "canceled")
                                    self.delete_position(pos['id'], cancel_api=False)
                                    removed_count += 1

                    # 매수 상위 2건, 매도 최하위 2건씩 탐색 시작 (체결 시 자동 확장)
                    _smart_sync_kis(buys, 2)
                    _smart_sync_kis(sells, 2)
                                
                    return {"status": "success", "message": f"한투 스마트 동기화 완료 (체결/취소 {removed_count}건 업데이트)"}
                else:
                    return {"status": "error", "message": f"거래소 조회 실패: {open_res.get('msg1')}"}

            elif exchange == "bithumb" and self.bithumb:
                db_positions = self.get_positions()
                removed_count = 0
                
                # 매수/매도 분리 후 현재가에 가장 가까운 순서로 정렬
                # 매수(buy)는 비쌀수록 현재가에 가까움 (내림차순)
                buys = sorted([p for p in db_positions if p['side'] == 'buy'], key=lambda x: float(x['avg_price']), reverse=True)
                # 매도(sell)는 쌀수록 현재가에 가까움 (오름차순)
                sells = sorted([p for p in db_positions if p['side'] == 'sell'], key=lambda x: float(x['avg_price']))

                def _smart_sync(sorted_pos, max_check=2):
                    nonlocal removed_count
                    unfilled_checked = 0
                    for pos in sorted_pos:
                        if unfilled_checked >= max_check:
                            break
                            
                        order_id = pos.get('order_id')
                        if not order_id:
                            continue
                            
                        try:
                            res = self.bithumb.get_order(order_id)
                            state = res.get('state')
                            
                            if state == 'done':
                                logger.info(f"[빗썸 동기화] 체결 확인됨 (uuid: {order_id}) -> DB 이동 및 핑퐁 생성")
                                self.record_trade(pos['symbol'], pos['quantity'], pos['avg_price'], pos['side'], mode_key, "filled")
                                self.delete_position(pos['id'], cancel_api=False)
                                removed_count += 1
                                
                                # 핑퐁 반대 주문 발송
                                self._place_pingpong_order("bithumb", pos['symbol'], pos['side'], pos['avg_price'], pos['quantity'], mode_key)
                                
                                # 체결된 경우 unfilled_checked 카운트를 올리지 않음 -> 자연스럽게 다음 호가(추가 1건)를 더 조회하게 됨!
                            elif state == 'cancel':
                                logger.info(f"[빗썸 동기화] 취소 확인됨 (uuid: {order_id}) -> DB 이동")
                                self.record_trade(pos['symbol'], pos['quantity'], pos['avg_price'], pos['side'], mode_key, "canceled")
                                self.delete_position(pos['id'], cancel_api=False)
                                removed_count += 1
                                # 취소된 경우도 카운트를 올리지 않아 다음 호가를 탐색함
                            else:
                                # wait 등 아직 체결되지 않은 주문을 확인했을 때만 카운트 증가
                                unfilled_checked += 1
                        except Exception as e:
                            logger.error(f"[빗썸 동기화] 개별 조회 에러 {order_id}: {e}")
                            # 에러 시 무한 루프나 과다 요청을 막기 위해 체크 카운트 증가
                            unfilled_checked += 1
                            
                # 매수 상위 2건, 매도 최하위 2건씩 탐색 시작
                _smart_sync(buys, 2)
                _smart_sync(sells, 2)
                        
                return {"status": "success", "message": f"빗썸 스마트 동기화 완료 (체결/취소 {removed_count}건 업데이트)"}

        except Exception as e:
            return {"status": "error", "message": f"동기화 중 오류 발생: {str(e)}"}
            
        return {"status": "success", "message": "해당 모드는 아직 동기화가 구현되지 않았습니다."}

    async def run_loop(self):
        logger.info("Trader Loop is now running...")
        
        import time  # 루프 밖에서 1회만 임포트 (루프 내 반복 임포트 방지)
        last_sync_time = 0  # 초기값을 0으로 두어 시작 직후 즉시 동기화 실행되도록 함

        while self.running:
            try:
                import datetime
                now = datetime.datetime.now()
                exchange = self.config.get("exchange", "kis")
                
                # 한국투자증권(kis)인 경우 08:00 ~ 20:00 에만 동기화 및 매매 실행 (주간+넥스트장 포함)
                if exchange == "kis":
                    if now.hour < 8 or now.hour >= 20:
                        # 비거래 시간에는 1분(60초)마다 루프를 돌되 아무 작업도 하지 않음
                        await asyncio.sleep(60)
                        continue

                current_time = time.time()
                
                symbol = self.config.get("symbol", "042660")
                mock_mode = self.config.get("mock_mode", True)
                
                # 설정된 주기(기본 1분)마다 잔고 및 서버 미체결 내역 자동 동기화
                sync_interval_mins = int(self.config.get("auto_sync_interval", 1))
                sync_interval_secs = sync_interval_mins * 60
                
                if current_time - last_sync_time >= sync_interval_secs:
                    # DB에 활성화된 미체결 포지션이 있는지 확인
                    active_positions = self.get_positions()
                    
                    if not active_positions:
                        logger.info("🔄 [자동 동기화 스킵] 활성화된 포지션(미체결 주문)이 없어 동기화를 건너뜁니다.")
                    else:
                        logger.info("🔄 [자동 동기화] 잔고 및 거래소 미체결 내역 동기화 실행")
                        self.update_balance()
                        self.sync_orders()
                    
                    last_sync_time = current_time
                
                ex_cfg = self.config.get(exchange, {})
                grid_interval = ex_cfg.get("grid_interval", 2000 if exchange == "kis" else 10)
                take_profit = ex_cfg.get("take_profit", 2000 if exchange == "kis" else 10)
                order_quantity = ex_cfg.get("order_quantity", 10 if exchange == "kis" else 1000)
                
                # 1. Fetch Price
                current_price = 0
                if exchange == "kis" and self.kis:
                    price_res = self.kis.get_current_price(symbol)
                    if isinstance(price_res, dict):
                        if "output" in price_res and isinstance(price_res["output"], dict):
                            current_price = float(price_res["output"].get("stck_prpr", 0))
                        else:
                            logger.warning(f"KIS Price Response Error: {price_res.get('msg1', price_res)}")
                            current_price = 0
                    else:
                        try:
                            current_price = float(price_res)
                        except (ValueError, TypeError):
                            current_price = 0
                elif exchange == "bithumb" and self.bithumb:
                    try:
                        current_price = float(self.bithumb.get_current_price(symbol))
                    except (ValueError, TypeError):
                        current_price = 0
                else:
                    logger.warning(f"Exchange {exchange} not ready.")
                    await asyncio.sleep(3)
                    continue
                    
                if current_price <= 0:
                    await asyncio.sleep(3)
                    continue
                    
                # 1.5. 서버 기동 시 등 기준가가 0이면 현재가로 즉시 초기화
                if not ex_cfg.get("base_price") or ex_cfg.get("base_price") == 0:
                    self.update_config({exchange: {"base_price": int(current_price)}})
                    logger.info(f"🔄 [설정 갱신] {exchange} 기준가가 실시간 현재가({int(current_price)})로 초기화되었습니다.")

                # 2. Get Open Positions (Bullets)
                positions = self.get_positions()
                symbol_positions = [p for p in positions if p['symbol'] == symbol]
                # 3. Trade Logic (그리드 주문 체결 감지 및 시뮬레이션)
                for pos in symbol_positions:
                    p_id = pos['id']
                    p_price = pos['avg_price']
                    p_side = pos['side']
                    p_qty = pos['quantity']
                    
                    # 매도 주문: 현재가가 매도 지정가보다 높거나 같아지면 체결
                    if p_side == "sell" and current_price >= p_price:
                        logger.info(f"[체결 감지] 🔵 매도 그리드 도달: {p_price}원 (현재가 {current_price})")
                        self.record_trade(symbol, p_qty, p_price, p_side, self._get_mode_key(), "filled")
                        self.delete_position(p_id, cancel_api=False)
                        self._place_pingpong_order(exchange, symbol, p_side, p_price, p_qty, self._get_mode_key())
                        
                    # 매수 주문: 현재가가 매수 지정가보다 낮거나 같아지면 체결
                    elif p_side == "buy" and current_price <= p_price:
                        logger.info(f"[체결 감지] 🔴 매수 그리드 도달: {p_price}원 (현재가 {current_price})")
                        self.record_trade(symbol, p_qty, p_price, p_side, self._get_mode_key(), "filled")
                        self.delete_position(p_id, cancel_api=False)
                        self._place_pingpong_order(exchange, symbol, p_side, p_price, p_qty, self._get_mode_key())

                await asyncio.sleep(3) # 3초마다 감시
            except Exception as e:
                logger.error(f"Error in Trader Loop: {e}")
                await asyncio.sleep(3)
                
        logger.info("Trader Loop Stopped.")

# Singleton instance for the server to use
trader = TraderLoop()
