@echo off
echo Starting Windows 11 System Telemetry Dashboard...
echo.
echo Checking Python installation...
python --version
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.7 or higher
    pause
    exit /b 1
)

echo.
echo Checking dependencies...
python -c "import psutil, wmi; print('Dependencies OK')"
if %errorlevel% neq 0 (
    echo Installing dependencies...
    pip install -r requirements.txt
)

echo.
echo Launching dashboard...
python dashboard.py

echo.
echo Dashboard closed.
pause