# Windows 11 System Telemetry Dashboard - Project Files

This document lists all the files created for the Windows 11 System Telemetry Dashboard project.

## Core Application Files

### [`dashboard.py`](dashboard.py)
- **Main application file** containing the complete dashboard implementation
- Features real-time system monitoring with 500ms updates
- Includes GUI with dark theme and color-coded status indicators
- Monitors: CPU usage, memory, disk I/O, network activity, and temperatures
- Uses threading for non-blocking data collection

### [`requirements.txt`](requirements.txt)
- **Dependencies file** listing required Python packages
- Contains: `psutil>=5.9.0` and `WMI>=1.5.1`
- Use with: `pip install -r requirements.txt`

## Launcher and Utility Files

### [`launch_dashboard.py`](launch_dashboard.py)
- **User-friendly launcher** with dependency checking
- Automatically installs missing dependencies
- Provides helpful error messages and troubleshooting tips
- Recommended way to start the dashboard

### [`run_dashboard.bat`](run_dashboard.bat)
- **Windows batch file** for easy launching
- Checks Python installation and dependencies
- Alternative launcher for Windows users

### [`test_metrics.py`](test_metrics.py)
- **Testing script** to verify metrics collection
- Tests all system monitoring functions
- Useful for troubleshooting and validation

## Documentation

### [`README.md`](README.md)
- **Complete documentation** with installation and usage instructions
- Includes feature descriptions, troubleshooting guide, and technical details
- Contains color coding explanations and customization tips

### [`project_files.md`](project_files.md)
- **This file** - overview of all project components

## Quick Start

1. **Easy Launch**: Run `python launch_dashboard.py`
2. **Manual Launch**: Run `python dashboard.py`
3. **Windows Batch**: Double-click `run_dashboard.bat`

## System Requirements

- Windows 11 (or Windows 10)
- Python 3.7 or higher
- Administrator privileges (recommended for temperature monitoring)

## Key Features

- ✅ Real-time monitoring (500ms updates)
- ✅ CPU usage, frequency, and per-core statistics
- ✅ Memory usage with detailed breakdown
- ✅ Disk I/O speeds and usage percentage
- ✅ Network upload/download speeds and totals
- ✅ System temperature monitoring (with fallback estimation)
- ✅ System uptime display
- ✅ Color-coded status indicators (green/orange/red)
- ✅ Dark theme optimized for extended use
- ✅ Low resource usage and efficient data collection
- ✅ Windows 11 optimized with WMI integration

## File Sizes and Line Counts

- `dashboard.py`: 458 lines - Complete application
- `launch_dashboard.py`: 67 lines - User-friendly launcher
- `test_metrics.py`: 73 lines - Testing and validation
- `README.md`: 147 lines - Comprehensive documentation
- `requirements.txt`: 2 lines - Dependencies
- `run_dashboard.bat`: 23 lines - Windows batch launcher

Total: ~770 lines of code and documentation