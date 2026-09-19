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
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("TraderLoop")

load_dotenv()

class TraderLoop:
    def __init__(self):
        self.running = False
        self.balances = {"kis": 0, "bithumb": 0}  # 거래소별 잔고 캐시
        default_ex = os.getenv("DEFAULT_EXCHANGE", "kis")
        default_mock = os.getenv("MOCK_MODE", "true").lower() in ("true", "1", "yes")
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
            # 기존 테이블 마이그레이션: side, exchange_mode 컬럼 추가
            for col, default in [("side", "'buy'"), ("exchange_mode", "'kis_mock'")]:
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
                "SELECT id, symbol, quantity, buy_price, side FROM grid_bullets WHERE exchange_mode = ?",
                (mode_key,)
            )
            rows = cursor.fetchall()
            return [{"id": r[0], "symbol": r[1], "quantity": r[2], "avg_price": r[3], "side": r[4] or "buy"} for r in rows]

    def save_position(self, symbol, quantity, buy_price, side="buy"):
        mode_key = self._get_mode_key()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO grid_bullets (symbol, quantity, buy_price, side, exchange_mode)
                VALUES (?, ?, ?, ?, ?)
            ''', (symbol, quantity, buy_price, side, mode_key))
            conn.commit()

    def delete_position(self, position_id):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('DELETE FROM grid_bullets WHERE id = ?', (position_id,))
            conn.commit()

    def delete_all_positions(self):
        """현재 모드의 포지션만 전체 삭제"""
        mode_key = self._get_mode_key()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('DELETE FROM grid_bullets WHERE exchange_mode = ?', (mode_key,))
            conn.commit()


    def update_balance(self):
        exchange = self.config.get("exchange", "kis")
        self.balances[exchange] = 0  # 초기화
        
        if exchange == "kis" and self.kis:
            try:
                bal_data = self.kis.get_balance()
                if bal_data.get('rt_cd') == '0':
                    self.balances["kis"] = int(bal_data['output2'][0]['dnca_tot_amt'])
                else:
                    logger.error(f"KIS Balance Error: {bal_data}")
            except Exception as e:
                logger.error(f"KIS Balance exception: {e}")
                
        elif exchange == "bithumb" and self.bithumb:
            try:
                bal_data = self.bithumb.get_balance()
                # (total_krw, in_use_krw, available_krw, total_coin)
                self.balances["bithumb"] = int(bal_data[2])
            except Exception as e:
                logger.error(f"Bithumb Balance fetch error: {e}")

    def get_status(self):
        # UI 조회 속도를 위해 네트워크 통신(update_balance)을 빼고, 메모리에 캐싱된 값만 즉시 반환
        current_exchange = self.config.get("exchange", "kis")
        is_connected = False
        if current_exchange == "kis":
            is_connected = self.kis is not None
        elif current_exchange == "bithumb":
            is_connected = self.bithumb is not None
        bal = self.balances.get(current_exchange, 0)

        return {
            "running": self.running,
            "config": self.config,
            "balance": bal,
            "positions": self.get_positions(),
            "exchange_connected": is_connected
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
            if exchange == "kis":
                if isinstance(api_res, dict) and api_res.get("rt_cd") == "0":
                    is_success = True
                    msg = api_res.get("msg1", "성공")
            elif exchange == "bithumb":
                if isinstance(api_res, dict) and api_res.get("status") == "0000":
                    is_success = True
                    msg = "성공"

            if is_success:
                self.save_position(symbol, quantity, price or 0, side=side)  # 매수/매도 모두 DB 기록
                return {"status": "success", "message": f"{order_type} 주문 체결 접수 성공: {msg}"}
            else:
                return {"status": "error", "message": f"주문 실패: {msg}"}
                
        except Exception as e:
            logger.error(f"Manual Order Error: {e}")
            return {"status": "error", "message": f"주문 실행 중 오류: {e}"}

    def cancel_all_orders(self):
        """현재 모드의 미체결 주문 일괄 취소 및 DB 초기화"""
        mode_key = self._get_mode_key()
        self.delete_all_positions()
        logger.info(f"[{mode_key}] 포지션 및 미체결 주문 일괄 취소 (DB 초기화)")
        return {"status": "success", "message": f"미체결 주문 및 포지션이 초기화되었습니다. ({mode_key})"}

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
                today = datetime.datetime.now().strftime("%Y%M%d")
                
                # 1. 미체결 주문 조회 (현재 살아있는 주문)
                open_res = self.kis.get_open_orders()
                # 2. 당일 체결 내역 조회 (이미 체결된 주문)
                # 실제 API에서 11월은 %m 이어야 하므로 포맷 수정: %Y%m%d
                today = datetime.datetime.now().strftime("%Y%m%d")
                filled_res = self.kis.get_daily_orders(today, today)
                
                if open_res.get("rt_cd") == "0" and filled_res.get("rt_cd") == "0":
                    open_list = open_res.get("output", [])
                    filled_list = filled_res.get("output1", []) if "output1" in filled_res else filled_res.get("output", [])
                    
                    open_prices = [float(o.get("ord_unpr", 0)) for o in open_list]
                    filled_prices = [float(o.get("ord_unpr", 0)) for o in filled_list]
                    
                    db_positions = self.get_positions()
                    removed_count = 0
                    for pos in db_positions:
                        p_price = float(pos['avg_price'])
                        p_qty = float(pos['quantity'])
                        p_side = pos['side']
                        p_symbol = pos['symbol']
                        
                        # [이중 점검 로직]
                        # 조건 1: 살아있는 미체결 리스트에 없음 (즉, 없어짐)
                        if p_price not in open_prices:
                            # 조건 2: 당일 체결 내역에는 존재함 (즉, 진짜로 체결됨)
                            if p_price in filled_prices:
                                logger.info(f"[동기화] 체결 확인됨 (가격: {p_price}) -> DB 히스토리 이동")
                                self.record_trade(p_symbol, p_qty, p_price, p_side, mode_key, "filled")
                                self.delete_position(pos['id'])
                                removed_count += 1
                            else:
                                # 체결 내역에도 없고 미체결 내역에도 없으면 취소된 주문으로 간주
                                logger.info(f"[동기화] 취소된 주문 확인 (가격: {p_price}) -> DB 히스토리 이동(canceled)")
                                self.record_trade(p_symbol, p_qty, p_price, p_side, mode_key, "canceled")
                                self.delete_position(pos['id'])
                                removed_count += 1
                                
                    return {"status": "success", "message": f"서버 동기화 완료 (체결/취소 {removed_count}건 이중 점검 업데이트)"}
                else:
                    return {"status": "error", "message": f"거래소 조회 실패: {open_res.get('msg1')}"}
                    
        except Exception as e:
            return {"status": "error", "message": f"동기화 중 오류 발생: {str(e)}"}
            
        return {"status": "success", "message": "해당 모드는 아직 동기화가 구현되지 않았습니다."}

    async def run_loop(self):
        logger.info("Trader Loop is now running...")
        
        last_sync_time = 0  # 초기값을 0으로 두어 시작 직후 즉시 동기화 실행되도록 함

        while self.running:
            try:
                import time
                current_time = time.time()
                
                # 설정된 주기(기본 30분)마다 잔고 및 서버 미체결 내역 자동 동기화
                sync_interval_mins = int(self.config.get("auto_sync_interval", 30))
                sync_interval_secs = sync_interval_mins * 60
                
                if current_time - last_sync_time >= sync_interval_secs:
                    logger.info("🔄 [자동 동기화] 잔고 및 거래소 미체결 내역 동기화 실행")
                    # 잔고 동기화 (느린 API 호출)
                    self.update_balance()
                    # 미체결 주문 동기화 (느린 API 호출)
                    self.sync_orders()
                    last_sync_time = current_time

                exchange = self.config.get("exchange", "kis")
                symbol = self.config.get("symbol", "042660")
                mock_mode = self.config.get("mock_mode", True)
                
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
                        self.delete_position(p_id)
                        
                    # 매수 주문: 현재가가 매수 지정가보다 낮거나 같아지면 체결
                    elif p_side == "buy" and current_price <= p_price:
                        logger.info(f"[체결 감지] 🔴 매수 그리드 도달: {p_price}원 (현재가 {current_price})")
                        self.record_trade(symbol, p_qty, p_price, p_side, self._get_mode_key(), "filled")
                        self.delete_position(p_id)

                await asyncio.sleep(3) # 3초마다 감시
            except Exception as e:
                logger.error(f"Error in Trader Loop: {e}")
                await asyncio.sleep(3)
                
        logger.info("Trader Loop Stopped.")

# Singleton instance for the server to use
trader = TraderLoop()
