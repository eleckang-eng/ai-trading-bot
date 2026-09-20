@echo off
chcp 65001 > nul
title [웹 서버 및 대시보드] 자동매매 통합 관제
cd /d %~dp0

echo ========================================================
echo   [독립 실행] 백엔드(FastAPI) 및 대시보드(Streamlit)
echo   제미나이 AI 어시스턴트 세션과 무관하게 영구 구동됩니다.
echo ========================================================
echo.

:: 1. 백엔드 API 서버를 별도 독립 프로세스 창으로 실행
start "AI Trading Bot - Backend API" cmd /k "cd /d %~dp0 && uvicorn server.api_server:app --host 0.0.0.0 --port 8000"

:: 2. 스트림릿 대시보드를 별도 독립 프로세스 창으로 실행
start "AI Trading Bot - Streamlit Dashboard" cmd /k "cd /d %~dp0 && streamlit run app/dashboard.py --server.port 8501"

echo 백엔드(포트 8000) 및 대시보드(포트 8501)가 각각 독립된 창으로 실행되었습니다.
echo 브라우저에서 http://localhost:8501 로 접속하여 이용하십시오.
echo.
timeout /t 3 > nul

