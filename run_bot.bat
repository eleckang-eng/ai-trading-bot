@echo off
chcp 65001 >nul
echo ==============================================
echo       AI Trading Bot - Restart Script
echo ==============================================

echo [1/2] Cleaning up existing processes...
:: 8000 포트(FastAPI) 강제 종료
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000 "') do (
    taskkill /F /PID %%a 2>nul
)

:: 8501 포트(Streamlit) 강제 종료
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8501 "') do (
    taskkill /F /PID %%a 2>nul
)

:: 8080 포트(Mock Server) 강제 종료
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8080 "') do (
    taskkill /F /PID %%a 2>nul
)

:: 포트 반환을 위해 1초 대기
timeout /t 1 /nobreak >nul

echo.
echo [2/2] Starting AI Trading Bot Suite (main.py)...
start cmd /k "python main.py"

echo.
echo The entire trading suite (API, UI, Mock Exchange) has been restarted!
echo You can now access the dashboard at: http://localhost:8501
echo.
pause
