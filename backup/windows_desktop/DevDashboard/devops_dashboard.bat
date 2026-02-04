@echo off
REM DevOps Dashboard Launcher
REM Full system monitoring, log compression, WS storage, load balancing, WSL I/O

echo Starting DevOps Dashboard...
wsl.exe -d Ubuntu bash -l -c "cd /home/manoj/DevWorkspaces/dashboard && powershell.exe -ExecutionPolicy Bypass -File devops_dashboard.ps1"
pause
