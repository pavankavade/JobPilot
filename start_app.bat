@echo off
title JobPilot Web Server (Port 8000)
color 0A
echo ================================================================
echo   Starting JobPilot Web Application Server...
echo ================================================================
echo.
echo URL: http://localhost:8000
echo.
echo Press Ctrl+C to stop the server.
echo.
python server.py
pause
