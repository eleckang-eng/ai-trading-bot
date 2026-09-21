import subprocess
import sys
import time
import os

def main():
    print("Starting AI Trading Bot Suite...")
    
    # 프로젝트 루트 경로를 절대경로로 확정 (어디서 실행하든 동일하게 동작)
    root_dir = os.path.dirname(os.path.abspath(__file__))
    
    use_mock = "--mock" in sys.argv
    
    mock_proc = None
    if use_mock:
        # 1. Mock 거래소 서버 시작 (빗썸/KIS 시뮬레이터)
        mock_proc = subprocess.Popen(
            [sys.executable, os.path.join(root_dir, "server", "mock_exchange_server.py")],
            cwd=root_dir
        )
        print("Mock Exchange Server started on port 8080")
    else:
        print("Skipping Mock Exchange Server (run with --mock to enable)")
    
    # 2. FastAPI 백엔드 서버 시작
    # cwd를 server/ 로 고정해야 uvicorn이 api_server:app 모듈을 정확히 인식함
    api_proc = subprocess.Popen(
        [sys.executable, "api_server.py"],
        cwd=os.path.join(root_dir, "server")
    )
    print("API Server started on port 8000")
    
    # 3. Streamlit 대시보드 시작
    # cwd를 루트로 고정하여 app/dashboard.py 경로가 올바르게 해석되도록 함
    ui_proc = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run",
         os.path.join(root_dir, "app", "dashboard.py"),
         "--server.port=8501"],
        cwd=root_dir
    )
    print("Dashboard started on port 8501")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down servers...")
        if mock_proc:
            mock_proc.terminate()
        api_proc.terminate()
        ui_proc.terminate()

if __name__ == "__main__":
    main()
