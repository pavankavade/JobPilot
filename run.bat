@echo off
title JobPilot Master Launcher
color 0A
echo ================================================================
echo   JobPilot - All-in-One Launcher
echo ================================================================
echo.
echo [1/2] Starting JobPilot Web Server (Port 8000)...
start "JobPilot Server" cmd /k "cd /d D:\git\jobsearch && python server.py"

timeout /t 2 /nobreak >NUL

echo [2/2] Starting Google Chrome with Remote Debugging (Port 9222)...
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="%USERPROFILE%\.chrome-debug" --no-first-run --no-default-browser-check "http://localhost:8000" "https://www.naukri.com" "https://www.linkedin.com"

echo.
echo ================================================================
echo  All systems launched!
echo  - Web App: http://localhost:8000
echo  - Debug Chrome: Port 9222
echo ================================================================
echo.
pause
