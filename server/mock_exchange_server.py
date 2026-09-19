import os
import time
import uuid
import random
import threading
from fastapi import FastAPI, Request
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="Mock Exchange Server")

# ── 가상 거래소 매칭 엔진 상태 ────────────────────────
# 실제 KIS/빗썸 서버처럼 동작하기 위한 내부 상태
class MockState:
    def __init__(self):
        # 한화오션(042660) 실제가와 비슷한 83500원에서 시작
        self.prices = {"042660": 83500.0, "ONDO": 1000.0}
        # 모멘텀(추세) 속성을 추가하여 가격이 부드럽게 이어지도록 (왔다갔다 방지)
        self.momentum = {"042660": 0.0, "ONDO": 0.0}
        self.balances = {"kis_krw": 10000000, "bithumb_krw": 10000000}
        self.orders = []
        self.filled = []
        self.last_orno = 10000
        self.lock = threading.Lock()
        
        # 백테스트 데이터 로드
        self.backtest_data = []
        self.backtest_index = 0
        self.load_backtest_data()

    def load_backtest_data(self):
        import csv
        try:
            csv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backtest', '042660_minute_data_full.csv')
            raw_prices = []
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    raw_prices.append(float(row['Close']))
            
            if not raw_prices: return

            # 1분을 1초로 압축하여 재생하며, 
            # 1/3 구간은 원본(1배), 1/3 구간은 변동성 2배(급락/급등), 1/3 구간은 역방향 -2배(미러링 급변)로 생성
            self.backtest_data = [raw_prices[0]]
            current_price = raw_prices[0]
            chunk_size = max(1, len(raw_prices) // 3)

            for i in range(1, len(raw_prices)):
                delta = raw_prices[i] - raw_prices[i-1]
                
                if i < chunk_size:
                    multiplier = 1.0    # 원본 그대로
                elif i < chunk_size * 2:
                    multiplier = 2.0    # 2배 변동성 구간
                else:
                    multiplier = -2.0   # -2배 변동성 (역방향) 구간

                current_price += (delta * multiplier)
                if current_price < 500: current_price = 500 # 상장폐지 방지
                
                # 호가 단위 100원 맞추기
                current_price = round(current_price / 100) * 100
                self.backtest_data.append(current_price)

            print(f"Loaded {len(self.backtest_data)} rows. Phases: 1x, 2x, -2x applied.")
        except Exception as e:
            print("Backtest data load failed:", e)

    def get_new_orno(self):
        self.last_orno += 1
        return str(self.last_orno)

    def tick(self):
        """1초마다 가격을 변동시키고 지정가를 체결시킴"""
        with self.lock:
            # 1. 가격 갱신 (백테스트 데이터 우선)
            if self.backtest_data:
                self.prices["042660"] = self.backtest_data[self.backtest_index]
                self.backtest_index = (self.backtest_index + 1) % len(self.backtest_data)
                
                # ONDO는 그냥 랜덤 워크 유지
                self.momentum["ONDO"] = self.momentum["ONDO"] * 0.8 + random.uniform(-0.001, 0.001)
                self.prices["ONDO"] = round(self.prices["ONDO"] * (1 + self.momentum["ONDO"]), 1)
            else:
                # 백테스트 데이터가 없으면 기존 부드러운 랜덤 워크
                for sym in self.prices:
                    noise = random.uniform(-0.001, 0.001)
                    self.momentum[sym] = self.momentum[sym] * 0.8 + noise
                    new_p = self.prices[sym] * (1 + self.momentum[sym])
                    if sym == "042660":
                        new_p = round(new_p / 100) * 100
                    else:
                        new_p = round(new_p, 1)
                    self.prices[sym] = new_p

            # 2. 미체결 주문 매칭
            open_orders = [o for o in self.orders if o["status"] == "open"]
            for o in open_orders:
                curr_p = self.prices[o["symbol"]]
                matched = False
                if o["side"] == "buy" and curr_p <= o["price"]:
                    matched = True
                elif o["side"] == "sell" and curr_p >= o["price"]:
                    matched = True

                if matched:
                    o["status"] = "filled"
                    o["fill_time"] = time.strftime("%H%M%S")
                    o["fill_price"] = o["price"]
                    self.filled.append(o)
                    
                    # 잔고 업데이트 로직 (간소화)
                    # 여기서는 체결 상태만 제공하면 봇이 DB를 업데이트하므로 잔고는 크게 중요하지 않음

state = MockState()

def engine_loop():
    while True:
        state.tick()
        time.sleep(1.0)

threading.Thread(target=engine_loop, daemon=True).start()

# ── KIS Mock Endpoints ───────────────────────────────

@app.post("/oauth2/tokenP")
async def kis_token():
    return {"access_token": "mock_token_" + str(uuid.uuid4()), "expires_in": 86400}

@app.get("/uapi/domestic-stock/v1/quotations/inquire-price")
async def kis_price(FID_INPUT_ISCD: str = ""):
    price = state.prices.get(FID_INPUT_ISCD, 30000)
    return {"output": {"stck_prpr": str(int(price))}, "rt_cd": "0"}

@app.get("/uapi/domestic-stock/v1/trading/inquire-balance")
async def kis_balance():
    return {
        "output1": [],
        "output2": [{"dnca_tot_amt": str(state.balances["kis_krw"])}],
        "rt_cd": "0"
    }

@app.post("/uapi/domestic-stock/v1/trading/order-cash")
async def kis_order(req: Request):
    body = await req.json()
    symbol = body.get("PDNO")
    price = int(body.get("ORD_UNPR", 0))
    qty = int(body.get("ORD_QTY", 0))
    is_buy = "0802" in req.headers.get("tr_id", "")
    side = "buy" if is_buy else "sell"

    with state.lock:
        orno = state.get_new_orno()
        state.orders.append({
            "id": orno,
            "exchange": "kis",
            "symbol": symbol,
            "side": side,
            "price": price,
            "qty": qty,
            "status": "open",
            "time": time.strftime("%H%M%S")
        })

    return {
        "rt_cd": "0",
        "msg1": "모의주문 접수 완료",
        "output": {"ODNO": orno}
    }

@app.get("/uapi/domestic-stock/v1/trading/inquire-psbl-rvsecnl")
async def kis_open_orders():
    with state.lock:
        opens = [o for o in state.orders if o["exchange"] == "kis" and o["status"] == "open"]
        
    out1 = []
    for o in opens:
        out1.append({
            "odno": o["id"],
            "ord_tmd": o["time"],
            "ord_dvsn_name": "지정가",
            "sll_buy_dvsn_cd": "02" if o["side"] == "buy" else "01",
            "ord_qty": str(o["qty"]),
            "ord_unpr": str(o["price"]),
            "ccld_qty": "0",
            "tot_ccld_amt": "0"
        })
    return {"output": out1, "rt_cd": "0"}

@app.get("/uapi/domestic-stock/v1/trading/inquire-daily-ccld")
async def kis_daily_orders():
    with state.lock:
        fills = [o for o in state.filled if o["exchange"] == "kis"]
        
    out1 = []
    for o in fills:
        out1.append({
            "odno": o["id"],
            "ord_tmd": o["fill_time"],
            "sll_buy_dvsn_cd": "02" if o["side"] == "buy" else "01",
            "ord_qty": str(o["qty"]),
            "ord_unpr": str(o["price"]),
            "tot_ccld_qty": str(o["qty"]),
            "tot_ccld_amt": str(o["qty"] * o["price"])
        })
    return {"output1": out1, "rt_cd": "0"}

# ── Bithumb Mock Endpoints ────────────────────────────

@app.get("/public/ticker/{order_currency}_{payment_currency}")
async def bithumb_ticker(order_currency: str, payment_currency: str):
    price = state.prices.get(order_currency, 1000)
    return {"status": "0000", "data": {"closing_price": str(price)}}

@app.post("/info/balance")
async def bithumb_balance():
    return {"status": "0000", "data": {"available_krw": str(state.balances["bithumb_krw"]), "available_ONDO": "0"}}

@app.post("/trade/place")
async def bithumb_place_order(req: Request):
    form = await req.form()
    symbol = form.get("order_currency")
    price = float(form.get("price", 0))
    qty = float(form.get("units", 0))
    side = "buy" if form.get("type") == "bid" else "sell"

    with state.lock:
        orno = state.get_new_orno()
        state.orders.append({
            "id": orno,
            "exchange": "bithumb",
            "symbol": symbol,
            "side": side,
            "price": price,
            "qty": qty,
            "status": "open",
            "time": time.strftime("%H%M%S")
        })

    return {"status": "0000", "order_id": orno}

if __name__ == "__main__":
    uvicorn.run("mock_exchange_server:app", host="0.0.0.0", port=8080, reload=True)
