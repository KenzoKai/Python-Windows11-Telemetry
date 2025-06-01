@echo off
echo Arduino Telemetry Client Launcher
echo ==================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.7 or higher from https://python.org
    pause
    exit /b 1
)

echo Python found. Checking dependencies...

REM Check if psutil is installed
python -c "import psutil" >nul 2>&1
if errorlevel 1 (
    echo Installing required dependencies...
    pip install psutil
    if errorlevel 1 (
        echo ERROR: Failed to install psutil
        pause
        exit /b 1
    )
)

echo Dependencies OK. Starting telemetry client...
echo.
echo Instructions:
echo 1. Make sure your Arduino Giga R1 is connected to WiFi
echo 2. Note the IP address displayed on the Arduino screen
echo 3. Enter that IP address when prompted
echo.

python arduino_telemetry_client_multi_gpu.py

echo.
echo Telemetry client stopped.
pause