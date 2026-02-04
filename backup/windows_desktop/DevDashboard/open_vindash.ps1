# DevDashboard vindash Launcher (PowerShell)
# Run this to open vindash from Windows PowerShell

Write-Host "Opening vindash..." -ForegroundColor Cyan
wsl.exe -d Ubuntu -- bash -lc "source /home/manoj/.vindashrc && cd /home/manoj/DevWorkspaces && bash"

