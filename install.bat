@echo off
echo ========================================
echo   Mixpanel Bulk Event Replacer - Setup
echo ========================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% == 0 (
    echo [OK] Python is already installed.
) else (
    echo [!] Python not found. Downloading and installing Python...
    curl -L -o python_installer.exe https://www.python.org/ftp/python/3.12.0/python-3.12.0-amd64.exe
    python_installer.exe /quiet InstallAllUsers=0 PrependPath=1 Include_pip=1
    del python_installer.exe
    echo [OK] Python installed.
    echo.
    echo Please close this window and run install.bat again to continue.
    pause
    exit
)

echo.
echo [*] Installing Playwright...
pip install playwright >nul 2>&1
echo [OK] Playwright installed.

echo.
echo [*] Installing Chromium browser...
playwright install chromium
echo [OK] Chromium installed.

echo.
echo ========================================
echo   Setup complete! Run run.bat to start.
echo ========================================
pause
