@echo off
chcp 65001 > nul
title 자동매매 엔진 종료
cd /d %~dp0

echo ========================================================
echo   자동매매 프로세스를 종료합니다.
echo ========================================================
echo.

taskkill /F /FI "WINDOWTITLE eq [단독 실시간 콘솔]*" 2>nul
taskkill /F /FI "WINDOWTITLE eq [단독 실행]*" 2>nul
taskkill /F /FI "WINDOWTITLE eq AI Trading Bot*" 2>nul

echo 실행 중인 백그라운드 프로세스를 확인하고 정리합니다...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING 2^>nul') do taskkill /F /PID %%a 2>nul
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8501 ^| findstr LISTENING 2^>nul') do taskkill /F /PID %%a 2>nul

echo 종료되었습니다.
pause

