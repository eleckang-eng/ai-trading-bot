@echo off
chcp 65001 > nul
title 자동매매 상태 점검
cd /d %~dp0

echo ========================================================
echo   [상태 점검] 자동매매 단독 실행 프로세스 확인
echo ========================================================
echo.

echo 1. 현재 실행 중인 프로세스 목록:
tasklist /FI "IMAGENAME eq python.exe" /FO TABLE
echo.

echo 2. 최근 15줄 매매 및 시세 로그 (trading_bot.log):
echo --------------------------------------------------------
if exist trading_bot.log (
    powershell -Command "Get-Content trading_bot.log -Tail 15"
) else (
    echo 아직 생성된 로그 파일이 없습니다.
)
echo --------------------------------------------------------
echo.
pause

