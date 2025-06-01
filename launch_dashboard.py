#!/usr/bin/env python3
"""
Simple launcher for the Windows 11 System Telemetry Dashboard
Handles dependency checking and provides user-friendly error messages
"""

import sys
import subprocess
import importlib.util

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 7):
        print("Error: Python 3.7 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    return True

def check_dependency(package_name, install_name=None):
    """Check if a package is installed"""
    if install_name is None:
        install_name = package_name
    
    spec = importlib.util.find_spec(package_name)
    if spec is None:
        print(f"Missing dependency: {package_name}")
        try:
            print(f"Installing {install_name}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", install_name])
            return True
        except subprocess.CalledProcessError:
            print(f"Failed to install {install_name}")
            return False
    return True

def main():
    """Main launcher function"""
    print("Windows 11 System Telemetry Dashboard Launcher")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        input("Press Enter to exit...")
        return
    
    # Check dependencies
    dependencies = [
        ("psutil", "psutil>=5.9.0"),
        ("wmi", "WMI>=1.5.1")
    ]
    
    print("Checking dependencies...")
    all_deps_ok = True
    for package, install_name in dependencies:
        if not check_dependency(package, install_name):
            all_deps_ok = False
    
    if not all_deps_ok:
        print("\nSome dependencies could not be installed.")
        print("Please install them manually using:")
        print("pip install -r requirements.txt")
        input("Press Enter to exit...")
        return
    
    print("All dependencies satisfied!")
    print("\nStarting dashboard...")
    print("=" * 50)
    
    # Import and run the dashboard
    try:
        from dashboard import main as dashboard_main
        dashboard_main()
    except KeyboardInterrupt:
        print("\nDashboard stopped by user")
    except Exception as e:
        print(f"\nError running dashboard: {e}")
        print("\nTroubleshooting tips:")
        print("1. Make sure you're running as administrator for temperature monitoring")
        print("2. Check that all dependencies are properly installed")
        print("3. Verify your Python installation")
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()