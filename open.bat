git@echo off
title Django Dev Server

:: ============================================================
::  CHANGE THESE TWO PATHS ONLY
:: ============================================================
set VENV_DIR=F:\students\voorhees\D_V\expense_tracker\.venv\Scripts\activate.bat
set PROJECT_DIR=F:\students\voorhees\D_V\expense_tracker\clothing_expense_tracker
:: ============================================================

set PORT=8000

echo.
echo  =============================================
echo   Django Dev Server
echo   Venv    : %VENV_DIR%
echo   Project : %PROJECT_DIR%
echo   Port    : %PORT%
echo  =============================================
echo.

:: Activate virtual environment
if not exist "%VENV_DIR%" (
    echo  [ERROR] Venv not found:
    echo          %VENV_DIR%
    pause
    exit /b 1
)
call "%VENV_DIR%"
echo  [OK] Virtual environment activated.
echo.

:: Go to project folder (where manage.py lives)
cd /d "%PROJECT_DIR%"
if errorlevel 1 (
    echo  [ERROR] Project folder not found:
    echo          %PROJECT_DIR%
    pause
    exit /b 1
)

:: Confirm manage.py is here
if not exist "manage.py" (
    echo  [ERROR] manage.py not found in:
    echo          %PROJECT_DIR%
    echo.
    echo  Run this in CMD to locate it:
    echo  dir /s /b "%PROJECT_DIR%\manage.py"
    pause
    exit /b 1
)
echo  [OK] manage.py found.
echo.

:: Open browser after delay
start "" cmd /c "timeout /t 3 >nul && start http://127.0.0.1:%PORT%"
echo  [OK] Browser opens in 3 seconds...
echo.

:: Start Django server
echo  [OK] Starting server  --  press CTRL+C to stop
echo  -----------------------------------------------
python manage.py runserver %PORT%

echo.
echo  [INFO] Server stopped.
pause
