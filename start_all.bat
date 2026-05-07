@echo off
echo ==============================================
echo       Starting Mini SIEM Services
echo ==============================================

echo [1/3] Starting FastAPI Backend on Port 8000...
start "SIEM Backend" cmd /k "cd /d d:\security\siem_backend && python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

echo [2/3] Starting React Frontend on Port 5173...
start "SIEM Frontend" cmd /k "cd /d d:\security\siem_frontend && npm run dev"

echo [3/3] Starting Log Generator...
start "SIEM Log Generator" cmd /k "cd /d d:\security && python log_generator.py --attack-mode"

echo.
echo All services have been launched in separate terminal windows!
echo You can view your live dashboard at: http://localhost:5173
echo.
echo Note: If you want to simulate an active attack, close the Log Generator window
echo and run "python log_generator.py --attack-mode" in that folder.
echo.
pause
