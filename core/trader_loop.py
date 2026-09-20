import asyncio
import sqlite3
import os
import logging
from dotenv import load_dotenv
from typing import List, Dict

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("TraderLoop")

load_dotenv()

def adjust_kis_tick(price: float, is_buy: bool) -> int:
    """
    Adjust the target price to the nearest KIS specific tick for Hanwha Ocean grid.
    SELL: ends in 900
    BUY: ends in 100
    """
    p_int = int(price)
    base = (p_int // 1000) * 1000
    if is_buy:
        # Ends in 100
        cand1 = base - 900 # (base - 1000 + 100)
        cand2 = base + 100
        cand3 = base + 1100
        cands = [cand1, cand2, cand3]
        return min(cands, key=lambda x: abs(p_int - x))
    else:
        # Ends in 900
        cand1 = base - 100 # (base - 1000 + 900)
        cand2 = base + 900
        cand3 = base + 1900
        cands = [cand1, cand2, cand3]
        return min(cands, key=lambda x: abs(p_int - x))

class TraderLoop:
    def __init__(self):
        self.running = False
        self.config = {
            "symbol": "005930",
            "exchange": "KIS", # KIS or BITHUMB
            "mode": "real", # real, mock, test
            "auto_sync_interval": 60, # 1 minute sleep interval
            "grid_interval": 2000, 
            "quantity": 10
        }
        self.state = {
            "current_price": 0.0,
            "api_fail_count": 0,
            "critical_alert": None
        }
        self.db_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
        os.makedirs(self.db_dir, exist_ok=True)
        self.db_path = os.path.join(self.db_dir, 'positions.db')
        self._init_db()
        self.loop_task = None

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            # Active open orders we are tracking
            conn.execute('''
                CREATE TABLE IF NOT EXISTS open_orders (
                    order_id TEXT PRIMARY KEY,
                    symbol TEXT,
                    side TEXT,
                    price REAL,
                    quantity INTEGER,
                    status TEXT
                )
            ''')
            # Historical positions/executions
            conn.execute('''
                CREATE TABLE IF NOT EXISTS positions (
                    symbol TEXT PRIMARY KEY,
                    quantity INTEGER,
                    avg_price REAL
                )
            ''')
            conn.commit()

    def get_open_orders_db(self) -> List[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT order_id, symbol, side, price, quantity FROM open_orders WHERE status='open'")
            rows = cursor.fetchall()
            return [{"order_id": r[0], "symbol": r[1], "side": r[2], "price": r[3], "quantity": r[4]} for r in rows]

    def add_open_order_db(self, order_id, symbol, side, price, quantity):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO open_orders (order_id, symbol, side, price, quantity, status)
                VALUES (?, ?, ?, ?, ?, 'open')
            ''', (order_id, symbol, side, price, quantity))
            conn.commit()

    def mark_order_executed_db(self, order_id):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("UPDATE open_orders SET status='executed' WHERE order_id=?", (order_id,))
            conn.commit()

    def mark_order_cancelled_db(self, order_id):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("UPDATE open_orders SET status='cancelled' WHERE order_id=?", (order_id,))
            conn.commit()

    def get_status(self):
        return {
            "running": self.running,
            "config": self.config,
            "state": self.state
        }

    def start(self):
        if not self.running:
            self.running = True
            self.loop_task = asyncio.create_task(self.run_loop())
            logger.info("TraderLoop started in Low-Power Polling mode.")
        return self.get_status()

    def stop(self):
        if self.running:
            self.running = False
            logger.info("TraderLoop stop requested.")
        return self.get_status()

    def update_config(self, config_updates):
        self.config.update(config_updates)
        return self.config
        
    async def fetch_exchange_data(self):
        # TODO: Implement actual API calls to KIS / Bithumb
        max_retries = 3
        for attempt in range(max_retries):
            try:
                logger.info("Fetching current price, open orders, and execution history from exchange...")
                # Mock responses for demonstration
                return {
                    "current_price": 80000,
                    "exchange_open_orders": [], # List of open order IDs on the exchange
                    "execution_history": [] # List of executed order IDs today
                }
            except Exception as e:
                wait_time = 2 ** attempt
                logger.warning(f"fetch_exchange_data API call failed: {e}. Retrying in {wait_time}s... ({attempt+1}/{max_retries})")
                await asyncio.sleep(wait_time)
        raise Exception("Fetch exchange data failed after max retries")
        
    async def place_order(self, symbol, side, price, quantity):
        # TODO: Implement actual API call to place order
        import uuid
        order_id = str(uuid.uuid4())
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                logger.info(f"Placing {side} order for {symbol} at {price} x {quantity}. OrderID: {order_id}")
                self.add_open_order_db(order_id, symbol, side, price, quantity)
                return
            except Exception as e:
                wait_time = 2 ** attempt
                logger.warning(f"place_order API call failed: {e}. Retrying in {wait_time}s... ({attempt+1}/{max_retries})")
                await asyncio.sleep(wait_time)
        raise Exception("Order placement failed after max retries")

    def _evaluate_algorithm_rules(self):
        """
        Use self.state['current_price'] to make algorithmic decisions,
        such as dynamic grid expansion or spawning new stair-step orders.
        """
        current_price = self.state.get("current_price", 0)
        if current_price == 0:
            return
            
        # Example logic placeholder:
        # if current_price < lower_bound:
        #    spawn_new_grid(...)
        logger.debug(f"Algorithm rules checked for price: {current_price}")

    async def run_loop(self):
        logger.info("Low-Power Polling Grid Bot is active.")
        from datetime import datetime, timezone, timedelta
        kst_tz = timezone(timedelta(hours=9))
        
        while self.running:
            try:
                exchange = self.config.get("exchange", "KIS").upper()
                if exchange == "KIS":
                    now_kst = datetime.now(kst_tz)
                    if not (8 <= now_kst.hour < 20):
                        logger.info("Outside KIS operating hours (08:00~20:00 KST). Skipping sync and sleeping.")
                        interval = self.config.get("auto_sync_interval", 60)
                        for _ in range(interval):
                            if not self.running:
                                break
                            await asyncio.sleep(1)
                        continue
                
                # 1. WAKE UP & SYNC
                logger.info("--- Starting Sync Cycle ---")
                
                # Fetch data from exchange
                ex_data = await self.fetch_exchange_data()
                
                # Success - clear error state
                self.state['api_fail_count'] = 0
                self.state['critical_alert'] = None
                
                self.state["current_price"] = ex_data.get("current_price", 0.0)
                exchange_open_orders = set(ex_data["exchange_open_orders"])
                execution_history = set(ex_data["execution_history"])
                
                # Algorithmic Decisions based on current price
                logger.info(f"Current Price updated to: {self.state['current_price']}. Evaluating algorithm rules...")
                self._evaluate_algorithm_rules()
                
                # Fetch local DB open orders
                local_open_orders = self.get_open_orders_db()
                
                # 2. RECONCILIATION
                for order in local_open_orders:
                    order_id = order["order_id"]
                    
                    # 1st Check: Missing in exchange open orders?
                    if order_id not in exchange_open_orders:
                        # 2nd Check: Is it in execution history?
                        if order_id in execution_history: 
                            logger.info(f"Execution Confirmed for Order {order_id} ({order['side']} at {order['price']})")
                            self.mark_order_executed_db(order_id)
                            
                            # 3. PING-PONG LOGIC
                            grid_interval = self.config.get("grid_interval", 2000)
                            exchange = self.config.get("exchange", "KIS")
                            
                            if order["side"] == "BUY":
                                target_price = order["price"] + (grid_interval * 2)
                                if exchange == "KIS":
                                    target_price = adjust_kis_tick(target_price, is_buy=False)
                                await self.place_order(order["symbol"], "SELL", target_price, order["quantity"])
                                await asyncio.sleep(1.0) # Rate limit protection for multiple executions
                                
                            elif order["side"] == "SELL":
                                target_price = order["price"] - (grid_interval * 2)
                                if exchange == "KIS":
                                    target_price = adjust_kis_tick(target_price, is_buy=True)
                                await self.place_order(order["symbol"], "BUY", target_price, order["quantity"])
                                await asyncio.sleep(1.0) # Rate limit protection for multiple executions
                        else:
                            # Order is missing from Exchange Open Orders AND Execution History
                            # Meaning it was cancelled or expired
                            logger.warning(f"Order {order_id} not found in open orders or execution history. Marking as cancelled.")
                            self.mark_order_cancelled_db(order_id)

                logger.info("--- Sync Cycle Completed ---")
                
            except Exception as e:
                logger.error(f"Error during Sync Cycle: {e}")
                self.state['api_fail_count'] += 1
                if self.state['api_fail_count'] >= 5:
                    self.state['critical_alert'] = "API 연속 5회 통신 실패. 긴급 점검 요망"
                    logger.critical(self.state['critical_alert'])
                
            # 4. DEEP SLEEP
            interval = self.config.get("auto_sync_interval", 60)
            logger.info(f"Going to deep sleep for {interval} seconds...")
            # Break sleep into smaller chunks to allow responsive shutdown
            for _ in range(interval):
                if not self.running:
                    break
                await asyncio.sleep(1)
                
        logger.info("Trader Loop Stopped.")

# Singleton instance for the server to use
trader = TraderLoop()
