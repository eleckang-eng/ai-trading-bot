import subprocess
import sys
import time
import os

def main():
    print("Starting AI Trading Bot Suite...")
    
    # 1. Start Mock Exchange Server
    mock_proc = subprocess.Popen([sys.executable, "server/mock_exchange_server.py"])
    print("Mock Exchange Server started on port 8080")
    
    # 2. Start API Server
    # api_server uses uvicorn.run("api_server:app"), so we must run it in server directory
    api_proc = subprocess.Popen([sys.executable, "api_server.py"], cwd="server")
    print("API Server started on port 8000")
    
    # 3. Start Streamlit Dashboard
    ui_proc = subprocess.Popen([sys.executable, "-m", "streamlit", "run", "app/dashboard.py", "--server.port=8501", "--server.headless=true"])
    print("Dashboard started on port 8501")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down servers...")
        mock_proc.terminate()
        api_proc.terminate()
        ui_proc.terminate()

if __name__ == "__main__":
    main()
