@echo off
title Syncora AI Backend Server
echo ========================================================
echo  Syncora AI - College Hackathon Coordinator Backend
echo ========================================================
echo.
cd /d "%~dp0\backend"
python run_server.py || py run_server.py
pause
