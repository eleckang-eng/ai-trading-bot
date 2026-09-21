@echo off
setlocal

echo ==============================================
echo       AI Trading Bot - Start Script
echo ==============================================

set "ROOT=%~dp0"
set "PYTHON=%ROOT%venv\Scripts\python.exe"

echo [1/3] Stopping existing processes...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000 "') do taskkill /F /PID %%a 2>nul
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8501 "') do taskkill /F /PID %%a 2>nul
timeout /t 1 /nobreak > nul

echo [2/3] Starting FastAPI Backend (Port 8000)...
start "API Server" cmd /k "cd /d "%ROOT%server" && "%PYTHON%" api_server.py"

timeout /t 2 /nobreak > nul

echo [3/3] Starting Streamlit Dashboard (Port 8501)...
start "Dashboard" cmd /k "%PYTHON% -m streamlit run "%ROOT%app\dashboard.py" --server.port=8501"

echo.
echo Server started successfully!
echo Dashboard: http://localhost:8501
echo.
pause
