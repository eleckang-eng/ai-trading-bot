import asyncio
import sqlite3
import os
import logging
from dotenv import load_dotenv
from typing import List, Dict

# 로그 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("TraderLoop")

load_dotenv()

def adjust_kis_tick(price: float, is_buy: bool) -> int:
    """
    한국투자증권(KIS) 특정 호가 단위(Tick)에 맞춰 가격을 반올림/보정하는 함수.
    Ping-Pong 봇 특성상 지정가 체결을 빠르고 확실하게 가져가기 위해, 
    매도 시에는 끝자리가 900(예: 83900), 매수 시에는 끝자리가 100(예: 80100)이 되도록
    수학적으로 가장 가까운 틱 가격을 계산하여 반환합니다.
    """
    p_int = int(price)
    base = (p_int // 1000) * 1000
    if is_buy:
        # 매수(BUY): 끝자리를 무조건 100으로 맞추어 체결 우선순위 및 그리드 효율을 높임
        cand1 = base - 900 # (base - 1000 + 100)
        cand2 = base + 100
        cand3 = base + 1100
        cands = [cand1, cand2, cand3]
        return min(cands, key=lambda x: abs(p_int - x))
    else:
        # 매도(SELL): 끝자리를 무조건 900으로 맞추어 체결 우선순위 및 이익 실현을 최적화함
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
            "exchange": "KIS", # KIS 또는 BITHUMB
            "mode": "real", # 실전(real), 모의(mock), 백테스트(test)
            "auto_sync_interval": 60, # 기본 1분마다 깨어나서 동기화(Low-Power Polling)
            "grid_interval": 2000, 
            "quantity": 10
        }
        self.state = {
            "current_price": 0.0,
            "api_fail_count": 0, # API 통신 연속 실패 횟수 누적
            "critical_alert": None # 에러 임계치 초과 시 발령되는 긴급 알림 메시지
        }
        self.db_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
        os.makedirs(self.db_dir, exist_ok=True)
        self.db_path = os.path.join(self.db_dir, 'positions.db')
        self._init_db()
        self.loop_task = None

    def _init_db(self):
        """SQLite 데이터베이스 초기화. 미체결 주문과 누적 포지션을 영속화하여 앱 종료 후에도 상태를 잃지 않도록 방어합니다."""
        with sqlite3.connect(self.db_path) as conn:
            # 추적 중인 미체결 주문
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
            # 과거 누적 포지션 및 평단가 기록
            conn.execute('''
                CREATE TABLE IF NOT EXISTS positions (
                    symbol TEXT PRIMARY KEY,
                    quantity INTEGER,
                    avg_price REAL
                )
            ''')
            conn.commit()

    def get_open_orders_db(self) -> List[Dict]:
        """로컬 DB에서 현재 '미체결(open)' 상태로 마킹된 주문 목록을 조회합니다."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT order_id, symbol, side, price, quantity FROM open_orders WHERE status='open'")
            rows = cursor.fetchall()
            return [{"order_id": r[0], "symbol": r[1], "side": r[2], "price": r[3], "quantity": r[4]} for r in rows]

    def add_open_order_db(self, order_id, symbol, side, price, quantity):
        """거래소에 신규 주문을 넣은 직후 로컬 DB에 'open' 상태로 안전하게 기록합니다."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO open_orders (order_id, symbol, side, price, quantity, status)
                VALUES (?, ?, ?, ?, ?, 'open')
            ''', (order_id, symbol, side, price, quantity))
            conn.commit()

    def mark_order_executed_db(self, order_id):
        """거래소에서 해당 주문이 완전 체결되었음을 확인(Reconciliation)했을 때 상태를 업데이트합니다."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("UPDATE open_orders SET status='executed' WHERE order_id=?", (order_id,))
            conn.commit()

    def mark_order_cancelled_db(self, order_id):
        """
        주문 만료 방어 로직:
        장 마감(15:30)으로 인해 거래소에서 자동 취소되었거나 사용자가 HTS에서 임의로 취소하여
        미체결에도 없고 체결 내역에도 없는 증발한 주문을 'cancelled'로 처리하여 Ping-Pong 오작동을 막습니다.
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("UPDATE open_orders SET status='cancelled' WHERE order_id=?", (order_id,))
            conn.commit()

    def get_status(self):
        """FastAPI 백엔드를 통해 현재 봇의 상태(설정, 진행 여부, 에러 알림 등)를 외부로 반환합니다."""
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
        """
        거래소 통신(가격, 미체결, 체결내역 동시 조회)
        단일 실패 시 시스템을 멈추지 않고, Exponential Backoff(지수 백오프: 1초, 2초, 4초 대기) 기법을 적용하여
        네트워크 일시 단절이나 500 내부 서버 오류를 스스로 극복(Self-healing)하도록 설계되었습니다.
        """
        max_retries = 3
        for attempt in range(max_retries):
            try:
                logger.info("Fetching current price, open orders, and execution history from exchange...")
                # TODO: 실제 KIS/Bithumb API 연동 코드가 이곳에 들어갑니다.
                return {
                    "current_price": 80000,
                    "exchange_open_orders": [], # 현재 거래소에 걸려있는 미체결 주문 ID 목록
                    "execution_history": [] # 당일 체결이 완료된 주문 ID 목록
                }
            except Exception as e:
                wait_time = 2 ** attempt # 1초, 2초, 4초 점진적 대기
                logger.warning(f"fetch_exchange_data API call failed: {e}. Retrying in {wait_time}s... ({attempt+1}/{max_retries})")
                await asyncio.sleep(wait_time)
        raise Exception("Fetch exchange data failed after max retries")
        
    async def place_order(self, symbol, side, price, quantity):
        """
        지정가 주문 접수.
        마찬가지로 지수 백오프 방어 로직을 두어, 일시적인 Rate Limit이나 네트워크 타임아웃 발생 시
        안전하게 잠시 대기했다가 다시 찔러보도록 유도합니다.
        """
        import uuid
        order_id = str(uuid.uuid4())
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                logger.info(f"Placing {side} order for {symbol} at {price} x {quantity}. OrderID: {order_id}")
                # TODO: 실제 API 접수 호출 부
                
                # 접수 완료 시 안전하게 DB에 기록
                self.add_open_order_db(order_id, symbol, side, price, quantity)
                return
            except Exception as e:
                wait_time = 2 ** attempt
                logger.warning(f"place_order API call failed: {e}. Retrying in {wait_time}s... ({attempt+1}/{max_retries})")
                await asyncio.sleep(wait_time)
        raise Exception("Order placement failed after max retries")

    def _evaluate_algorithm_rules(self):
        """
        UI 표시 용도가 아닌, 봇 자체 알고리즘 연산을 위한 함수입니다.
        캐싱된 self.state['current_price']를 이용해 주가가 그리드를 너무 멀리 이탈했는지 검사하거나,
        상황에 맞게 새로운 계단형 주문을 동적으로 생성(Dynamic Grid Expansion)하는 로직이 여기에 위치합니다.
        """
        current_price = self.state.get("current_price", 0)
        if current_price == 0:
            return
            
        # 예시: 현재가가 특정 하단 밴드를 이탈하면 추가 물타기 그리드를 배포하는 식의 확장 로직
        # if current_price < lower_bound:
        #    spawn_new_grid(...)
        logger.debug(f"Algorithm rules checked for price: {current_price}")

    async def run_loop(self):
        """
        메인 코어 루프 (Low-Power Polling Grid Bot)
        무한 루프에 의한 배터리 낭비(Busy-waiting)를 없애기 위해 1회의 완벽한 동기화(Sync) 사이클 후
        지정된 시간(기본 1분) 동안 Deep Sleep 모드에 들어가는 아키텍처입니다.
        """
        logger.info("Low-Power Polling Grid Bot is active.")
        from datetime import datetime, timezone, timedelta
        kst_tz = timezone(timedelta(hours=9))
        
        while self.running:
            try:
                # [운영시간 방어] 한국투자증권(KIS)은 정규장 시간에만 움직여야 하므로 불필요한 API 낭비를 막습니다.
                exchange = self.config.get("exchange", "KIS").upper()
                if exchange == "KIS":
                    now_kst = datetime.now(kst_tz)
                    # 08:00 AM ~ 20:00 PM 사이가 아닐 경우 API 호출을 전면 생략하고 동면합니다.
                    if not (8 <= now_kst.hour < 20):
                        logger.info("Outside KIS operating hours (08:00~20:00 KST). Skipping sync and sleeping.")
                        interval = self.config.get("auto_sync_interval", 60)
                        for _ in range(interval):
                            if not self.running:
                                break
                            await asyncio.sleep(1)
                        continue
                
                # 1. WAKE UP & SYNC (기상 및 거래소 동기화)
                logger.info("--- Starting Sync Cycle ---")
                
                # 거래소에서 모든 정보(현재가, 미체결, 체결)를 한 번에 긁어옵니다.
                ex_data = await self.fetch_exchange_data()
                
                # 정상 통신 성공 시 기존에 쌓였던 에러 카운터와 긴급 알림을 모두 초기화(Self-healing)합니다.
                self.state['api_fail_count'] = 0
                self.state['critical_alert'] = None
                
                self.state["current_price"] = ex_data.get("current_price", 0.0)
                exchange_open_orders = set(ex_data["exchange_open_orders"])
                execution_history = set(ex_data["execution_history"])
                
                # 알고리즘 의사결정 호출
                logger.info(f"Current Price updated to: {self.state['current_price']}. Evaluating algorithm rules...")
                self._evaluate_algorithm_rules()
                
                # 로컬 DB에 기록되어 있는 우리의 미체결 주문 목록을 가져옵니다.
                local_open_orders = self.get_open_orders_db()
                
                # 2. RECONCILIATION (체결 교차 검증)
                # 로컬에는 '미체결'로 떠있는데, 거래소 데이터와 대조해봅니다.
                for order in local_open_orders:
                    order_id = order["order_id"]
                    
                    # 1차 검증: 거래소 미체결 목록에서 해당 주문이 감쪽같이 사라졌는가?
                    if order_id not in exchange_open_orders:
                        # 2차 검증: 취소된 게 아니라 당일 체결 내역(Execution History)에 정상적으로 존재하는가?
                        if order_id in execution_history: 
                            logger.info(f"Execution Confirmed for Order {order_id} ({order['side']} at {order['price']})")
                            self.mark_order_executed_db(order_id)
                            
                            # 3. PING-PONG LOGIC (그물망 타격 대응)
                            # 체결이 확인되었으므로, 해당 체결가를 기준으로 grid_interval * 2 만큼 떨어진 곳에 반대 포지션을 깝니다.
                            grid_interval = self.config.get("grid_interval", 2000)
                            exchange = self.config.get("exchange", "KIS")
                            
                            if order["side"] == "BUY":
                                target_price = order["price"] + (grid_interval * 2)
                                if exchange == "KIS":
                                    target_price = adjust_kis_tick(target_price, is_buy=False)
                                await self.place_order(order["symbol"], "SELL", target_price, order["quantity"])
                                # [Rate Limit 방어] 다수 주문이 동시 체결되어 연달아 핑퐁이 나갈 때, KIS 초당 제한을 피하기 위해 1.0초 지연을 줍니다.
                                await asyncio.sleep(1.0) 
                                
                            elif order["side"] == "SELL":
                                target_price = order["price"] - (grid_interval * 2)
                                if exchange == "KIS":
                                    target_price = adjust_kis_tick(target_price, is_buy=True)
                                await self.place_order(order["symbol"], "BUY", target_price, order["quantity"])
                                # [Rate Limit 방어] 다수 주문 접수 지연
                                await asyncio.sleep(1.0) 
                        else:
                            # 증발 현상 방어 (장 마감 만료 또는 유저 임의 취소)
                            # 미체결에도 없고 체결 내역에도 없으므로, 허위 핑퐁을 방지하기 위해 과감히 DB에서 'cancelled' 처리합니다.
                            logger.warning(f"Order {order_id} not found in open orders or execution history. Marking as cancelled.")
                            self.mark_order_cancelled_db(order_id)

                logger.info("--- Sync Cycle Completed ---")
                
            except Exception as e:
                # [긴급 정지 방어] 통신 실패 등 에러 발생 시 카운트를 누적하고 5회 이상(약 5분 불능) 시 크리티컬 에러를 발포합니다.
                logger.error(f"Error during Sync Cycle: {e}")
                self.state['api_fail_count'] += 1
                if self.state['api_fail_count'] >= 5:
                    self.state['critical_alert'] = "API 연속 5회 통신 실패. 긴급 점검 요망"
                    logger.critical(self.state['critical_alert'])
                
            # 4. DEEP SLEEP (깊은 수면)
            # 설정된 interval(예: 60초) 동안 봇은 아무런 네트워크 활동 없이 대기하여 모바일 리소스를 아낍니다.
            # 다만 긴급 정지(stop) 요청 시 1초 단위로 빠르게 반응할 수 있도록 루프를 쪼개서 대기합니다.
            interval = self.config.get("auto_sync_interval", 60)
            logger.info(f"Going to deep sleep for {interval} seconds...")
            for _ in range(interval):
                if not self.running:
                    break
                await asyncio.sleep(1)
                
        logger.info("Trader Loop Stopped.")

# 서버에서 글로벌하게 접근할 수 있도록 Singleton 인스턴스를 하나 둡니다.
trader = TraderLoop()
