@echo off
title LPBF Melt Pool Monitoring - One-Click Start

REM ============================================================
REM   One-click launcher for the LPBF Melt Pool Monitoring System
REM     Backend  : FastAPI  -> http://localhost:8000   docs: /docs
REM     Frontend : Vue3     -> http://localhost:5173
REM   First run: auto-installs dependencies and trains models.
REM ============================================================

REM -- Ensure we run from the project root --
cd /d "%~dp0"

echo ============================================================
echo   LPBF Melt Pool Monitoring System - One-Click Start
echo ============================================================
echo.

REM ---- 1. Check Python ----
where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.9+ and add it to PATH.
    pause
    exit /b 1
)

REM ---- 2. Check / install Python dependencies ----
echo [1/4] Checking Python dependencies ...
python -c "import fastapi, uvicorn, pydantic, numpy, pandas, sklearn, torch, torchvision, cv2, PIL, joblib" >nul 2>nul
if errorlevel 1 (
    echo [INFO] Installing Python dependencies - first run ...
    python -m pip install -r requirements.txt
)

REM ---- 3. Train models if missing ----
echo [2/4] Checking trained models ...
set NEED_TRAIN=0
if not exist "models\cnn_model.pth" set NEED_TRAIN=1
if not exist "models\regressor.joblib" set NEED_TRAIN=1
if "%NEED_TRAIN%"=="1" (
    echo [INFO] Models not found. Training - first run, a few minutes ...
    python -m src.train
)

REM ---- 4. Check / install frontend dependencies ----
echo [3/4] Checking frontend dependencies ...
if not exist "frontend\node_modules" (
    echo [INFO] Installing frontend dependencies - first run ...
    pushd frontend
    call npm install
    popd
)

REM ---- 5. Launch backend and frontend ----
echo [4/4] Launching backend and frontend ...
start "LPBF Backend" cmd /k python scripts\run_backend.py
start "LPBF Frontend" /d "%~dp0frontend" cmd /k npm run dev

echo.
echo ============================================================
echo   Started.
echo     Backend  : http://localhost:8000   docs: /docs
echo     Frontend : http://localhost:5173
echo   Close the two new windows to stop the services.
echo ============================================================
echo.
pause
