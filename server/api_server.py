from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
import uvicorn
import sys
import os

# Add parent directory to path to allow importing from core
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.trader_loop import trader

app = FastAPI(
    title="AI Trading Bot API",
    description="REST API for controlling the AI Trading Bot Core Loop",
    version="1.0.0"
)

class ConfigModel(BaseModel):
    symbol: str = None
    target_price: float = None
    # Add other config fields as needed

@app.on_event("startup")
async def startup_event():
    # 서버 기동 시 트레이딩 코어 루프 자동 실행 (AUTO_START=true 설정 시)
    auto_start = os.getenv("AUTO_START", "false").lower() in ("true", "1", "yes")
    if auto_start:
        trader.start()

@app.on_event("shutdown")
async def shutdown_event():
    trader.stop()

@app.get("/status")
def get_status():
    """Get the current status of the trader loop and positions."""
    return trader.get_status()

@app.post("/start")
async def start_trader():
    """Start the 24-hour trading core loop."""
    return trader.start()

@app.post("/stop")
async def stop_trader():
    """Stop the trading core loop."""
    return trader.stop()

from typing import Dict, Any

@app.post("/config")
def update_config(payload: dict):
    """설정 변경"""
    return trader.update_config(payload)

@app.get("/price")
def get_price(exchange: str, symbol: str):
    """현재가 단건 조회 (UI 렌더링용)"""
    try:
        price = 0
        if exchange == "kis" and trader.kis:
            res = trader.kis.get_current_price(symbol)
            if isinstance(res, dict) and "output" in res:
                price = float(res["output"]["stck_prpr"])
            else:
                price = float(res)
        elif exchange == "bithumb" and trader.bithumb:
            price = float(trader.bithumb.get_current_price(symbol))
        return {"price": price}
    except Exception as e:
        return {"price": 0, "error": str(e)}

@app.post("/refresh_balance")
def refresh_balance():
    """수동 잔고 동기화: 현재 선택된 거래소의 잔고를 API로부터 갱신한다."""
    trader.update_balance()
    exchange = trader.config.get("exchange", "kis")
    return {"status": "success", "balance": trader.balances.get(exchange, 0)}

class OrderModel(BaseModel):
    side: str  # "buy" or "sell"
    quantity: float
    price: float = None  # None이면 시장가

from typing import List
import uuid
import threading

class BatchOrderModel(BaseModel):
    orders: List[OrderModel]

import logging
logger = logging.getLogger(__name__)

import time

# 배치 주문 작업 상태를 메모리에 보관 (task_id -> 상태 dict)
_batch_tasks: dict = {}

def _run_batch_orders(task_id: str, orders: list):
    """백그라운드 스레드에서 순차 주문 처리"""
    _batch_tasks[task_id]["status"] = "processing"
    results = []
    total = len(orders)
    for i, order in enumerate(orders):
        try:
            res = trader.manual_order(order.side, order.quantity, order.price)
            results.append(res)
        except Exception as e:
            results.append({"status": "error", "message": str(e)})
        _batch_tasks[task_id]["progress"] = i + 1
        _batch_tasks[task_id]["results"] = results
        # KIS API Rate Limit: 초당 5회 이하 (200ms 간격 + 여유 150ms)
        if i < total - 1:
            time.sleep(0.35)

    success_count = sum(1 for r in results if isinstance(r, dict) and r.get("status") == "success")
    _batch_tasks[task_id]["status"] = "done"
    _batch_tasks[task_id]["total"] = total
    _batch_tasks[task_id]["success_count"] = success_count
    _batch_tasks[task_id]["fail_count"] = total - success_count
    logger.info(f"[BATCH] task={task_id} 완료: {success_count}/{total} 성공")

@app.post("/order/batch")
def batch_order(payload: BatchOrderModel):
    """여러 건의 주문을 백그라운드 스레드에서 비동기 처리. 즉시 task_id 반환."""
    task_id = str(uuid.uuid4())[:8]
    _batch_tasks[task_id] = {
        "status": "queued",
        "total": len(payload.orders),
        "progress": 0,
        "results": [],
        "success_count": 0,
        "fail_count": 0,
    }
    t = threading.Thread(target=_run_batch_orders, args=(task_id, payload.orders), daemon=True)
    t.start()
    return {
        "status": "accepted",
        "task_id": task_id,
        "message": f"총 {len(payload.orders)}건 주문이 접수되었습니다. task_id로 진행 상황을 확인하세요."
    }

@app.get("/order/batch/status/{task_id}")
def batch_order_status(task_id: str):
    """배치 주문 진행 상황 조회"""
    task = _batch_tasks.get(task_id)
    if not task:
        return {"status": "not_found", "message": f"task_id={task_id}를 찾을 수 없습니다."}
    return {"task_id": task_id, **task}

@app.post("/order/manual")
def manual_order(order: OrderModel):
    """수동 주문 (매수/매도)"""
    try:
        return trader.manual_order(order.side, order.quantity, order.price)
    except Exception as e:
        import traceback
        print(f"MANUAL ORDER ERROR: {traceback.format_exc()}")
        return {"status": "error", "message": str(e)}

@app.post("/order/cancel_all")
def cancel_all_orders():
    """미체결 주문 일괄 취소"""
    return trader.cancel_all_orders()

@app.post("/order/sync")
def sync_orders():
    """거래소 서버와 미체결 주문 동기화"""
    return trader.sync_orders()

@app.post("/system/restart")
def restart_server():
    """봇 코어 루프 재시작"""
    import threading, time
    def _restart():
        trader.stop()
        time.sleep(2)  # 스레드 종료 및 정리 대기
        # 설정 등을 다시 불러오기 위해 필요하다면 여기서 로드
        trader.start()
    
    threading.Thread(target=_restart).start()
    return {"status": "success", "message": "봇 코어 루프 재시작 중..."}

if __name__ == "__main__":
    uvicorn.run("api_server:app", host="0.0.0.0", port=8000, reload=True)
