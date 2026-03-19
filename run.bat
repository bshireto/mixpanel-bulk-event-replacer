@echo off
echo ========================================
echo   Mixpanel Bulk Event Replacer
echo ========================================
echo.

:: Find Chrome
set CHROME_PATH=
if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" (
    set CHROME_PATH="C:\Program Files\Google\Chrome\Application\chrome.exe"
) else if exist "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" (
    set CHROME_PATH="C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
) else (
    echo [!] Chrome not found. Please install Google Chrome first.
    pause
    exit
)

echo [*] Closing any existing Chrome windows...
taskkill /F /IM chrome.exe >nul 2>&1
timeout /t 2 /nobreak >nul

echo [*] Launching Chrome...
start "" %CHROME_PATH% --remote-debugging-port=9222 --user-data-dir=C:\temp\mixpanel-debug
timeout /t 4 /nobreak >nul

echo.
echo ========================================
echo  Chrome is open. Now:
echo   1. Log into Mixpanel
echo   2. Navigate to the dashboard you want to update
echo   3. Scroll down to load all report cards
echo   4. Come back here and press Enter
echo ========================================
echo.
pause

echo.
echo [*] Running script...
python replace_events.py
