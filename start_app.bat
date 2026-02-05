@echo off
echo ==================================================
echo GST & Invoice Compliance System - Startup Script
echo ==================================================

REM Move to backend directory
cd /d %~dp0backend

echo.
echo [0/3] Activating virtual environment...
call .\venv\Scripts\activate

echo.
echo [1/3] Seeding Database...
python seed_data.py
if %errorlevel% neq 0 (
    echo Error seeding data. Installing dependencies...
    pip install -r requirements.txt
    python seed_data.py
)

echo.
echo [2/3] Starting Backend (FastAPI)...
start "Backend Server" cmd /k "call venv\Scripts\activate && python -m uvicorn main:app --reload"

echo.
echo [3/3] Starting Frontend (React)...
cd ../frontend
start "Frontend Server" cmd /k "npm run dev"

echo.
echo ==================================================
echo System Starting!
echo Backend: http://localhost:8000
echo Frontend: http://localhost:5173
echo ==================================================
pause
