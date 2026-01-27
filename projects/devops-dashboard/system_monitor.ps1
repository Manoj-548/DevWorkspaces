# System Monitor and Dashboard Module
# Real-time monitoring with WebSocket support

class SystemMonitor {
    [string]$LogPath
    [string]$StoragePath
    [hashtable]$WebSocketConnections
    [hashtable]$LoadBalancer
    [int]$RealTimeInterval = 1000  # milliseconds
    
    SystemMonitor() {
        $this.LogPath = "/home/manoj/DevWorkspaces/logs"
        $this.StoragePath = "/home/manoj/DevWorkspaces/storage"
        $this.WebSocketConnections = @{}
        $this.LoadBalancer = @{
            "CPU" = @{}
            "Memory" = @{}
            "Network" = @{}
        }
        $this.EnsureDirectories()
    }
    
    [void] EnsureDirectories() {
        New-Item -ItemType Directory -Force -Path $this.LogPath | Out-Null
        New-Item -ItemType Directory -Force -Path $this.StoragePath | Out-Null
        New-Item -ItemType Directory -Force -Path "$($this.StoragePath)/compressed" | Out-Null
        New-Item -ItemType Directory -Force -Path "$($this.StoragePath)/ws_cache" | Out-Null
    }
    
    [object] GetSystemStats() {
        $cpu = Get-WmiObject Win32_Processor | Measure-Object -Property LoadPercentage -Average | Select-Object Average
        $mem = Get-WmiObject Win32_ComputerSystem | Select-Object TotalPhysicalMemory
        $memUsed = (Get-WmiObject Win32_OperatingSystem).TotalVisibleMemorySize - (Get-WmiObject Win32_OperatingSystem).FreePhysicalMemory
        $memUsage = [math]::Round(($memUsed / $mem.TotalPhysicalMemory) * 100, 2)
        
        $disk = Get-WmiObject Win32_LogicalDisk | Where-Object {$_.DriveType -eq 3} | ForEach-Object {
            @{
                DeviceID = $_.DeviceID
                Size = [math]::Round($_.Size / 1GB, 2)
                FreeSpace = [math]::Round($_.FreeSpace / 1GB, 2)
                Usage = [math]::Round((($_.Size - $_.FreeSpace) / $_.Size) * 100, 2)
            }
        }
        
        return @{
            CPU = $cpu.Average
            Memory = $memUsage
            Disk = $disk
            Timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
        }
    }
    
    [string] CompressLogs([string]$SourcePath, [string]$ArchiveName) {
        $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
        $archivePath = "$($this.StoragePath)/compressed/${ArchiveName}_${timestamp}.7z"
        $7zPath = "C:\Program Files\7-Zip\7z.exe"
        
        if (Test-Path $7zPath) {
            & $7zPath a -t7z $archivePath $SourcePath -mx=9 | Out-Null
            return $archivePath
        } else {
            # Fallback to PowerShell compression
            Compress-Archive -Path $SourcePath -DestinationPath "$archivePath.zip" -Force
            return "$archivePath.zip"
        }
    }
    
    [void] StoreWebSocketData([string]$ConnectionId, [object]$Data) {
        $wsCachePath = "$($this.StoragePath)/ws_cache"
        $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
        $filePath = "$wsCachePath/${ConnectionId}_${timestamp}.json"
        
        $dataObj = @{
            ConnectionId = $ConnectionId
            Data = $Data
            Timestamp = $timestamp
        }
        
        $dataObj | ConvertTo-Json | Out-File -FilePath $filePath -Encoding UTF8
        
        # Manage efficiency - keep last 100 files per connection
        $files = Get-ChildItem -Path $wsCachePath -Filter "${ConnectionId}_*.json" | Sort-Object CreationTime -Descending
        if ($files.Count -gt 100) {
            $files | Select-Object -Skip 100 | Remove-Item -Force
        }
    }
    
    [object] GetLoadBalancedResource([string]$ResourceType) {
        $stats = $this.GetSystemStats()
        
        switch ($ResourceType) {
            "CPU" { return $stats.CPU }
            "Memory" { return $stats.Memory }
            "Network" { return $stats.Disk }
            default { return $stats }
        }
    }
    
    [void] WslIOOperation([string]$Command, [string]$Operation) {
        $wslResult = bash -c $Command 2>&1 | Out-String
        
        $logEntry = @{
            Command = $Command
            Operation = $Operation
            Result = $wslResult
            Timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
            Status = if ($LASTEXITCODE -eq 0) { "Success" } else { "Failed" }
        }
        
        $logEntry | ConvertTo-Json | Out-File -FilePath "$($this.LogPath)/wsl_io.log" -Append
    }
}

# Export for use in other scripts
$Global:SystemMonitor = [SystemMonitor]::new()
