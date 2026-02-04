@echo off
REM DevDashboard vindash Launcher
REM Run this to open vindash from Windows

echo Opening vindash...
wsl.exe -d Ubuntu -- bash -lc "source /home/manoj/.vindashrc && cd /home/manoj/DevWorkspaces && bash"

