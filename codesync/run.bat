@echo off
REM ───── CodeSync launcher for Windows ─────
cd /d "%~dp0"
echo.
echo === Installing dependencies (first run only) ===
python -m pip install --quiet -r requirements.txt
if errorlevel 1 (
    echo.
    echo [ERROR] Could not install dependencies. Make sure Python is installed and on PATH.
    pause
    exit /b 1
)
echo.
echo === Starting CodeSync ===
echo Open http://localhost:5000 in your browser
echo Press Ctrl+C to stop the server
echo.
python server.py
pause
