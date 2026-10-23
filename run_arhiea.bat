@echo off
title ARHIEA - ADAPTIVE ROAD AND HUMAN INTELLIGENCE EMERGENCY SYSTEM
color 0B

echo ===================================================================
echo   ARHIEA - ADAPTIVE ROAD AND HUMAN INTELLIGENCE EMERGENCY SYSTEM (SIH26204)
echo ===================================================================
echo Starting ARHIEA Core Engine and Dashboard on http://127.0.0.1:8000 ...
echo.

cd /d "%~dp0"

set PYTHON_BIN="%~dp0.venv\Scripts\python.exe"
if not exist %PYTHON_BIN% (
    set PYTHON_BIN=python
)

:: Start FastAPI Backend Server
start "ARHIEA Backend Server" %PYTHON_BIN% -m uvicorn backend.main:app --host 127.0.0.1 --port 8000

:: Wait 3 seconds for server to bind
timeout /t 3 /nobreak >nul

:: Open in default browser
start http://127.0.0.1:8000

echo.
echo ARHIEA is running!
echo Access the Dashboard at: http://127.0.0.1:8000
echo.
echo Press any key to stop ARHIEA...
pause >nul
taskkill /F /IM uvicorn.exe /T 2>nul
taskkill /F /FI "WINDOWTITLE eq ARHIEA Backend Server*" /T 2>nul
