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
    # You could optionally start the trader loop automatically on boot:
    # trader.start()
    pass

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
def update_config(config: Dict[str, Any]):
    """Update the trading configuration."""
    return trader.update_config(config)

@app.post("/refresh_balance")
def refresh_balance():
    """수동 잔고 동기화: 현재 선택된 거래소의 잔고를 API로부터 갱신한다."""
    trader.update_balance()
    exchange = trader.config.get("exchange", "kis")
    return {"status": "success", "balance": trader.balances.get(exchange, 0)}

if __name__ == "__main__":
    uvicorn.run("api_server:app", host="0.0.0.0", port=8000, reload=True)
