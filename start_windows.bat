@echo off
REM Windows startup script for the Distributed Task Queue System
REM This script starts the API server and workers

setlocal

REM Check if running in the correct directory
if not exist "main.py" (
    echo Error: Please run this script from the project root directory
    exit /b 1
)

REM Activate virtual environment if it exists
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else (
    echo Warning: Virtual environment not found. Make sure dependencies are installed.
)

REM Check if .env exists
if not exist ".env" (
    echo Creating .env from .env.example...
    copy .env.example .env
)

echo.
echo ============================================================
echo Distributed Task Queue System - Windows Startup
echo ============================================================
echo.
echo This will start all components. Please ensure:
echo 1. Redis is running (redis-server)
echo 2. Python 3.11+ is installed
echo 3. Dependencies are installed (pip install -r requirements.txt)
echo.
pause

REM Start components in separate windows
echo Starting FastAPI server...
start "Task Queue API Server" cmd /k "python main.py"

timeout /t 2 /nobreak

echo Starting worker process...
start "Task Queue Worker" cmd /k "python worker_main.py"

echo.
echo ============================================================
echo Services started! 
echo API available at: http://localhost:8000
echo API docs at: http://localhost:8000/docs
echo ============================================================
echo.

endlocal
