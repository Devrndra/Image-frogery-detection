@echo off
echo ==========================================
echo Starting Image Authentication System
echo ==========================================

echo Starting Backend Server...
start "Backend Server" cmd /k "py -3.11 -m uvicorn backend.main:app --reload"

echo Starting Frontend Application...
cd frontend
start "Frontend App" cmd /k "npm run dev"

echo ==========================================
echo System Started!
echo Backend: http://localhost:8000
echo Frontend: http://localhost:5173
echo ==========================================
pause
