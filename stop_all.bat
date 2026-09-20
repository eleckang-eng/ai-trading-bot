@echo off
chcp 65001 > nul
title 자동매매 시스템 일괄 종료
cd /d %~dp0

echo ========================================================
echo   실행 중인 자동매매 백엔드 및 대시보드를 일괄 종료합니다.
echo ========================================================
echo.

taskkill /F /FI "WINDOWTITLE eq AI Trading Bot - Backend API*" 2>nul
taskkill /F /FI "WINDOWTITLE eq AI Trading Bot - Streamlit Dashboard*" 2>nul
taskkill /F /FI "WINDOWTITLE eq [단독 실행] 한국투자/빗썸 자동매매 코어 엔진*" 2>nul

echo 포트 8000 (FastAPI) 및 8501 (Streamlit) 프로세스를 정리합니다...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING') do taskkill /F /PID %%a 2>nul
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8501 ^| findstr LISTENING') do taskkill /F /PID %%a 2>nul

echo 종료 작업이 완료되었습니다.
pause

