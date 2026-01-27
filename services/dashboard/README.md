# DevOps Dashboard

A comprehensive PowerShell-based dashboard for system monitoring, log management, WebSocket storage, load balancing, and WSL I/O operations.

## Features

### 1. System Monitor (Tab 1)
- Real-time CPU usage monitoring
- Memory usage tracking
- Disk space visualization
- Auto-refresh every 2 seconds

### 2. Log Compressor (Tab 2)
- Compress VS Code logs and system logs
- Archive to 7z format (with fallback to tar.gz)
- Custom archive naming with timestamps
- Storage location: `/home/manoj/DevWorkspaces/storage/compressed/`

### 3. WebSocket Manager (Tab 3)
- Store WebSocket connection data
- Efficiency management (keeps last 100 files per connection)
- JSON format storage
- Cache location: `/home/manoj/DevWorkspaces/storage/ws_cache/`

### 4. Storage Manager (Tab 4)
- View storage directory contents
- File size and usage tracking
- Refresh capability

### 5. WSL I/O Manager (Tab 5)
- Execute WSL commands from GUI
- Real-time output display
- Command history logging
- Logs to: `/home/manoj/DevWorkspaces/logs/wsl_io.log`

### 6. Load Balancer (Tab 6)
- Monitor CPU, Memory, Network loads
- Get scaling recommendations
- Real-time resource allocation status

## Usage

### Windows (Recommended)
```powershell
# Double-click devops_dashboard.bat
# OR run PowerShell:
powershell.exe -ExecutionPolicy Bypass -File "C:\path\to\devops_dashboard.ps1"
```

### WSL
```bash
# From WSL:
cd /home/manoj/DevWorkspaces/dashboard
./devops_dashboard.bat
```

## Directory Structure
```
dashboard/
├── system_monitor.ps1    # Core monitoring module
├── devops_dashboard.ps1  # Main GUI application
├── devops_dashboard.bat  # Windows launcher
└── README.md            # This file

/home/manoj/DevWorkspaces/
├── logs/                # System and WSL logs
├── storage/
│   ├── compressed/      # Compressed archives
│   └── ws_cache/        # WebSocket data cache
```

## Requirements
- Windows 10/11 with PowerShell 5.1+
- WSL (Windows Subsystem for Linux)
- 7-Zip (optional, for better compression)
- .NET Framework 4.5+

## Integration with Existing Dashboard
The DevOps Dashboard can be launched from the main DevDashboard by clicking the "DevOps Tools" button or by running `devops_dashboard.bat` directly.

## Real-time Features
- System stats update every 2 seconds
- All operations logged to `/home/manoj/DevWorkspaces/logs/`
- WebSocket data cached for efficiency
- Load balancing recommendations based on current resource usage
