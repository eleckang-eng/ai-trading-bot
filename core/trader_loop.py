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
        self.config = {"symbol": "ONDO", "exchange": "bithumb"} # Default changed to Bithumb for Phase 5
        self.balances = {"kis": 0, "bithumb": 0}  # 거래소별 잔고 캐시
        # DB setup
        self.db_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
        os.makedirs(self.db_dir, exist_ok=True)
        self.db_path = os.path.join(self.db_dir, 'positions.db')
        self._init_db()
        
        # KIS Setup
        self.url_base = os.getenv("KIS_URL_BASE", "")
        self.app_key = os.getenv("KIS_APP_KEY", "")
        self.app_secret = os.getenv("KIS_APP_SECRET", "")
        self.cano = os.getenv("KIS_CANO", "")
        self.acnt_prdt_cd = os.getenv("KIS_ACNT_PRDT_CD", "01")
        
        # Bithumb Setup
        self.bithumb_key = os.getenv("BITHUMB_API_KEY", "")
        self.bithumb_secret = os.getenv("BITHUMB_SECRET_KEY", "")

        self.loop_task = None
        
        try:
            self.kis = KISClient(self.url_base, self.app_key, self.app_secret, self.cano, self.acnt_prdt_cd)
        except Exception as e:
            logger.error(f"Failed to initialize KIS Client: {e}")
            self.kis = None
            
        try:
            if self.bithumb_key and self.bithumb_secret:
                self.bithumb = BithumbClient(self.bithumb_key, self.bithumb_secret)
            else:
                self.bithumb = None
        except Exception as e:
            logger.error(f"Failed to initialize Bithumb Client: {e}")
            self.bithumb = None

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS positions (
                    symbol TEXT PRIMARY KEY,
                    quantity INTEGER,
                    avg_price REAL
                )
            ''')
            conn.commit()

    def get_positions(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT symbol, quantity, avg_price FROM positions")
            rows = cursor.fetchall()
            return [{"symbol": r[0], "quantity": r[1], "avg_price": r[2]} for r in rows]

    def save_position(self, symbol, quantity, avg_price):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO positions (symbol, quantity, avg_price)
                VALUES (?, ?, ?)
                ON CONFLICT(symbol) DO UPDATE SET
                quantity=excluded.quantity,
                avg_price=excluded.avg_price
            ''', (symbol, quantity, avg_price))
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
        self.config.update(config_updates)
        return self.config

    async def run_loop(self):
        logger.info("Trader Loop is now running...")
        
        # Example initialization logic for real-time processing
        # approval_key = await self.get_kis_approval_key()
        
        while self.running:
            try:
                # TODO: Implement actual KIS WebSocket connection
                # async with websockets.connect(self.kis_ws_url) as ws:
                #    # Subscribe to price/execution data
                #    await ws.send(...)
                #    while self.running:
                #        msg = await ws.recv()
                #        self.process_ws_message(msg)
                
                # Simulating a heartbeat/tick
                logger.debug(f"Trader loop tick... (monitoring {self.config.get('symbol')})")
                
                # Mocking position update for demonstration
                # self.save_position(self.config.get('symbol'), 10, 75000.0)
                
                await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"Error in Trader Loop: {e}")
                await asyncio.sleep(5) # Delay before reconnecting
                
        logger.info("Trader Loop Stopped.")

# Singleton instance for the server to use
trader = TraderLoop()
