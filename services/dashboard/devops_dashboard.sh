#!/bin/bash
# DevOps Dashboard WSL Launcher

echo "Starting DevOps Dashboard..."
echo "This will launch the PowerShell GUI on Windows..."

# Get the Windows path equivalent
WINPATH=$(wslpath -w "$PWD")

# Launch the dashboard using PowerShell with Ubuntu distribution
wsl.exe -d Ubuntu bash -c "powershell.exe -ExecutionPolicy Bypass -File '${WINPATH}\\devops_dashboard.ps1'"

echo "Dashboard closed."
