@echo off
title JobPilot Chrome Debug Launcher (Port 9222)
color 0B
echo ================================================================
echo   JobPilot - Chrome Remote Debugging Launcher (Port 9222)
echo ================================================================
echo.
echo Launching Google Chrome in Debugging Mode...
echo Port: 9222
echo Profile Dir: %USERPROFILE%\.chrome-debug
echo.
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="%USERPROFILE%\.chrome-debug" --no-first-run --no-default-browser-check "http://localhost:8000" "https://www.naukri.com" "https://www.linkedin.com"

echo.
echo ================================================================
echo  SUCCESS! Chrome is running with Remote Debugging on Port 9222.
echo  Web App: http://localhost:8000
echo ================================================================
echo.
echo (You can log in to Naukri & LinkedIn once in this browser, and it will stay saved!)
echo.
pause
