@echo off
REM DevOps Dashboard Launcher
REM Comprehensive system monitoring, log compression, WSL I/O, and storage management

echo Starting DevOps Dashboard...
powershell.exe -ExecutionPolicy Bypass -File "%~dp0devops_dashboard.ps1"
pause
