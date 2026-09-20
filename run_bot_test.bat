@echo off
echo ==============================================
echo       AI Trading Bot - TEST MODE Script
echo ==============================================

echo [1/2] Cleaning up existing processes...
REM Kill process using port 8000
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000 "') do (
    taskkill /F /PID %%a 2>nul
)

REM Kill process using port 8501
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8501 "') do (
    taskkill /F /PID %%a 2>nul
)

REM Kill process using port 8080
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8080 "') do (
    taskkill /F /PID %%a 2>nul
)

REM Wait 1 second
timeout /t 1 /nobreak >nul

echo.
echo [2/2] Starting AI Trading Bot Suite (TEST MODE)...
start cmd /k "python main.py --mock"

echo.
echo The TEST trading suite (API, UI, Mock Exchange) has been restarted!
echo You can now access the dashboard at: http://localhost:8501
echo.
pause
