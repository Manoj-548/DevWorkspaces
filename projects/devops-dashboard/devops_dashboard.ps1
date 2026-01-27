# DevOps Dashboard - Comprehensive System Management
# Features: Log compression, WebSocket storage, Real-time monitoring, Load balancing, Storage manager

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
Add-Type -AssemblyName System.Web

$form = New-Object System.Windows.Forms.Form
$form.Text = "DevOps Dashboard - System Monitor & Manager"
$form.Size = New-Object System.Drawing.Size(1100, 700)
$form.StartPosition = "CenterScreen"
$form.BackColor = [System.Drawing.Color]::FromArgb(15, 23, 32)
$form.Font = New-Object System.Drawing.Font("Consolas", 9)

# Tab Control
$tabControl = New-Object System.Windows.Forms.TabControl
$tabControl.Location = New-Object System.Drawing.Point(10, 10)
$tabControl.Size = New-Object System.Drawing.Size(1060, 640)
$tabControl.BackColor = [System.Drawing.Color]::FromArgb(20, 30, 40)
$form.Controls.Add($tabControl)

# Tab 1: System Monitor
$tabMonitor = New-Object System.Windows.Forms.TabPage
$tabMonitor.Text = "System Monitor"
$tabMonitor.BackColor = [System.Drawing.Color]::FromArgb(20, 30, 40)
$tabMonitor.ForeColor = [System.Drawing.Color]::White
$tabControl.Controls.Add($tabMonitor)

# CPU Panel
$panelCPU = New-Object System.Windows.Forms.Panel
$panelCPU.Location = New-Object System.Drawing.Point(10, 10)
$panelCPU.Size = New-Object System.Drawing.Size(320, 150)
$panelCPU.BackColor = [System.Drawing.Color]::FromArgb(30, 40, 50)
$tabMonitor.Controls.Add($panelCPU)

$lblCPU = New-Object System.Windows.Forms.Label
$lblCPU.Text = "CPU Usage"
$lblCPU.Location = New-Object System.Drawing.Point(10, 10)
$lblCPU.ForeColor = [System.Drawing.Color]::FromArgb(0, 200, 255)
$lblCPU.Font = New-Object System.Drawing.Font("Consolas", 12, [System.Drawing.FontStyle]::Bold)
$panelCPU.Controls.Add($lblCPU)

$progressCPU = New-Object System.Windows.Forms.ProgressBar
$progressCPU.Location = New-Object System.Drawing.Point(10, 40)
$progressCPU.Size = New-Object System.Drawing.Size(300, 30)
$progressCPU.Style = "Continuous"
$panelCPU.Controls.Add($progressCPU)

$lblCPUValue = New-Object System.Windows.Forms.Label
$lblCPUValue.Text = "0%"
$lblCPUValue.Location = New-Object System.Drawing.Point(10, 80)
$lblCPUValue.ForeColor = [System.Drawing.Color]::White
$lblCPUValue.Font = New-Object System.Drawing.Font("Consolas", 24, [System.Drawing.FontStyle]::Bold)
$panelCPU.Controls.Add($lblCPUValue)

# Memory Panel
$panelMem = New-Object System.Windows.Forms.Panel
$panelMem.Location = New-Object System.Drawing.Point(340, 10)
$panelMem.Size = New-Object System.Drawing.Size(320, 150)
$panelMem.BackColor = [System.Drawing.Color]::FromArgb(30, 40, 50)
$tabMonitor.Controls.Add($panelMem)

$lblMem = New-Object System.Windows.Forms.Label
$lblMem.Text = "Memory Usage"
$lblMem.Location = New-Object System.Drawing.Point(10, 10)
$lblMem.ForeColor = [System.Drawing.Color]::FromArgb(0, 200, 255)
$lblMem.Font = New-Object System.Drawing.Font("Consolas", 12, [System.Drawing.FontStyle]::Bold)
$panelMem.Controls.Add($lblMem)

$progressMem = New-Object System.Windows.Forms.ProgressBar
$progressMem.Location = New-Object System.Drawing.Point(10, 40)
$progressMem.Size = New-Object System.Drawing.Size(300, 30)
$progressMem.Style = "Continuous"
$panelMem.Controls.Add($progressMem)

$lblMemValue = New-Object System.Windows.Forms.Label
$lblMemValue.Text = "0%"
$lblMemValue.Location = New-Object System.Drawing.Point(10, 80)
$lblMemValue.ForeColor = [System.Drawing.Color]::White
$lblMemValue.Font = New-Object System.Drawing.Font("Consolas", 24, [System.Drawing.FontStyle]::Bold)
$panelMem.Controls.Add($lblMemValue)

# Disk Panel
$panelDisk = New-Object System.Windows.Forms.Panel
$panelDisk.Location = New-Object System.Drawing.Point(670, 10)
$panelDisk.Size = New-Object System.Drawing.Size(360, 150)
$panelDisk.BackColor = [System.Drawing.Color]::FromArgb(30, 40, 50)
$tabMonitor.Controls.Add($panelDisk)

$lblDisk = New-Object System.Windows.Forms.Label
$lblDisk.Text = "Disk Usage"
$lblDisk.Location = New-Object System.Drawing.Point(10, 10)
$lblDisk.ForeColor = [System.Drawing.Color]::FromArgb(0, 200, 255)
$lblDisk.Font = New-Object System.Drawing.Font("Consolas", 12, [System.Drawing.FontStyle]::Bold)
$panelDisk.Controls.Add($lblDisk)

$txtDiskInfo = New-Object System.Windows.Forms.TextBox
$txtDiskInfo.Location = New-Object System.Drawing.Point(10, 40)
$txtDiskInfo.Size = New-Object System.Drawing.Size(340, 100)
$txtDiskInfo.BackColor = [System.Drawing.Color]::FromArgb(40, 50, 60)
$txtDiskInfo.ForeColor = [System.Drawing.Color]::White
$txtDiskInfo.Multiline = $true
$txtDiskInfo.ReadOnly = $true
$panelDisk.Controls.Add($txtDiskInfo)

# Tab 2: Log Compressor
$tabLogs = New-Object System.Windows.Forms.TabPage
$tabLogs.Text = "Log Compressor"
$tabLogs.BackColor = [System.Drawing.Color]::FromArgb(20, 30, 40)
$tabLogs.ForeColor = [System.Drawing.Color]::White
$tabControl.Controls.Add($tabLogs)

$lblLogSource = New-Object System.Windows.Forms.Label
$lblLogSource.Text = "Source Path:"
$lblLogSource.Location = New-Object System.Drawing.Point(10, 20)
$lblLogSource.ForeColor = [System.Drawing.Color]::White
$tabLogs.Controls.Add($lblLogSource)

$txtLogSource = New-Object System.Windows.Forms.TextBox
$txtLogSource.Location = New-Object System.Drawing.Point(120, 17)
$txtLogSource.Size = New-Object System.Drawing.Size(400, 25)
$txtLogSource.Text = "/home/manoj/DevWorkspaces/logs"
$tabLogs.Controls.Add($txtLogSource)

$lblArchiveName = New-Object System.Windows.Forms.Label
$lblArchiveName.Text = "Archive Name:"
$lblArchiveName.Location = New-Object System.Drawing.Point(530, 20)
$lblArchiveName.ForeColor = [System.Drawing.Color]::White
$tabLogs.Controls.Add($lblArchiveName)

$txtArchiveName = New-Object System.Windows.Forms.TextBox
$txtArchiveName.Location = New-Object System.Drawing.Point(640, 17)
$txtArchiveName.Size = New-Object System.Drawing.Size(200, 25)
$txtArchiveName.Text = "system_logs"
$tabLogs.Controls.Add($txtArchiveName)

$btnCompress = New-Object System.Windows.Forms.Button
$btnCompress.Text = "Compress Logs"
$btnCompress.Location = New-Object System.Drawing.Point(10, 55)
$btnCompress.Size = New-Object System.Drawing.Size(150, 35)
$btnCompress.BackColor = [System.Drawing.Color]::FromArgb(0, 150, 100)
$btnCompress.ForeColor = [System.Drawing.Color]::White
$tabLogs.Controls.Add($btnCompress)

$lblCompressionResult = New-Object System.Windows.Forms.Label
$lblCompressionResult.Location = New-Object System.Drawing.Point(10, 100)
$lblCompressionResult.Size = New-Object System.Drawing.Size(800, 300)
$lblCompressionResult.ForeColor = [System.Drawing.Color]::White
$tabLogs.Controls.Add($lblCompressionResult)

# Tab 3: WebSocket Manager
$tabWS = New-Object System.Windows.Forms.TabPage
$tabWS.Text = "WebSocket Manager"
$tabWS.BackColor = [System.Drawing.Color]::FromArgb(20, 30, 40)
$tabWS.ForeColor = [System.Drawing.Color]::White
$tabControl.Controls.Add($tabWS)

$lblWSId = New-Object System.Windows.Forms.Label
$lblWSId.Text = "Connection ID:"
$lblWSId.Location = New-Object System.Drawing.Point(10, 20)
$lblWSId.ForeColor = [System.Drawing.Color]::White
$tabWS.Controls.Add($lblWSId)

$txtWSId = New-Object System.Windows.Forms.TextBox
$txtWSId.Location = New-Object System.Drawing.Point(120, 17)
$txtWSId.Size = New-Object System.Drawing.Size(300, 25)
$tabWS.Controls.Add($txtWSId)

$btnStoreWS = New-Object System.Windows.Forms.Button
$btnStoreWS.Text = "Store WS Data"
$btnStoreWS.Location = New-Object System.Drawing.Point(430, 17)
$btnStoreWS.Size = New-Object System.Drawing.Size(150, 25)
$btnStoreWS.BackColor = [System.Drawing.Color]::FromArgb(0, 100, 200)
$btnStoreWS.ForeColor = [System.Drawing.Color]::White
$tabWS.Controls.Add($btnStoreWS)

$txtWSInfo = New-Object System.Windows.Forms.TextBox
$txtWSInfo.Location = New-Object System.Drawing.Point(10, 55)
$txtWSInfo.Size = New-Object System.Drawing.Size(1020, 400)
$txtWSInfo.BackColor = [System.Drawing.Color]::FromArgb(40, 50, 60)
$txtWSInfo.ForeColor = [System.Drawing.Color]::White
$txtWSInfo.Multiline = $true
$tabWS.Controls.Add($txtWSInfo)

# Tab 4: Storage Manager
$tabStorage = New-Object System.Windows.Forms.TabPage
$tabStorage.Text = "Storage Manager"
$tabStorage.BackColor = [System.Drawing.Color]::FromArgb(20, 30, 40)
$tabStorage.ForeColor = [System.Drawing.Color]::White
$tabControl.Controls.Add($tabStorage)

$lblStoragePath = New-Object System.Windows.Forms.Label
$lblStoragePath.Text = "Storage Path:"
$lblStoragePath.Location = New-Object System.Drawing.Point(10, 20)
$lblStoragePath.ForeColor = [System.Drawing.Color]::White
$tabStorage.Controls.Add($lblStoragePath)

$txtStoragePath = New-Object System.Windows.Forms.TextBox
$txtStoragePath.Location = New-Object System.Drawing.Point(120, 17)
$txtStoragePath.Size = New-Object System.Drawing.Size(400, 25)
$txtStoragePath.Text = "/home/manoj/DevWorkspaces/storage"
$tabStorage.Controls.Add($txtStoragePath)

$btnRefreshStorage = New-Object System.Windows.Forms.Button
$btnRefreshStorage.Text = "Refresh"
$btnRefreshStorage.Location = New-Object System.Drawing.Point(530, 17)
$btnRefreshStorage.Size = New-Object System.Drawing.Size(100, 25)
$tabStorage.Controls.Add($btnRefreshStorage)

$txtStorageInfo = New-Object System.Windows.Forms.TextBox
$txtStorageInfo.Location = New-Object System.Drawing.Point(10, 55)
$txtStorageInfo.Size = New-Object System.Drawing.Size(1020, 400)
$txtStorageInfo.BackColor = [System.Drawing.Color]::FromArgb(40, 50, 60)
$txtStorageInfo.ForeColor = [System.Drawing.Color]::White
$txtStorageInfo.Multiline = $true
$tabStorage.Controls.Add($txtStorageInfo)

# Tab 5: WSL I/O Manager
$tabWSL = New-Object System.Windows.Forms.TabPage
$tabWSL.Text = "WSL I/O Manager"
$tabWSL.BackColor = [System.Drawing.Color]::FromArgb(20, 30, 40)
$tabWSL.ForeColor = [System.Drawing.Color]::White
$tabControl.Controls.Add($tabWSL)

$lblWSLCommand = New-Object System.Windows.Forms.Label
$lblWSLCommand.Text = "WSL Command:"
$lblWSLCommand.Location = New-Object System.Drawing.Point(10, 20)
$lblWSLCommand.ForeColor = [System.Drawing.Color]::White
$tabWSL.Controls.Add($lblWSLCommand)

$txtWSLCommand = New-Object System.Windows.Forms.TextBox
$txtWSLCommand.Location = New-Object System.Drawing.Point(120, 17)
$txtWSLCommand.Size = New-Object System.Drawing.Size(700, 25)
$tabWSL.Controls.Add($txtWSLCommand)

$btnExecuteWSL = New-Object System.Windows.Forms.Button
$btnExecuteWSL.Text = "Execute"
$btnExecuteWSL.Location = New-Object System.Drawing.Point(830, 17)
$btnExecuteWSL.Size = New-Object System.Drawing.Size(100, 25)
$btnExecuteWSL.BackColor = [System.Drawing.Color]::FromArgb(0, 150, 100)
$btnExecuteWSL.ForeColor = [System.Drawing.Color]::White
$tabWSL.Controls.Add($btnExecuteWSL)

$txtWSLOutput = New-Object System.Windows.Forms.TextBox
$txtWSLOutput.Location = New-Object System.Drawing.Point(10, 55)
$txtWSLOutput.Size = New-Object System.Drawing.Size(1020, 400)
$txtWSLOutput.BackColor = [System.Drawing.Color]::FromArgb(40, 50, 60)
$txtWSLOutput.ForeColor = [System.Drawing.Color]::White
$txtWSLOutput.Multiline = $true
$tabWSL.Controls.Add($txtWSLOutput)

# Tab 6: Load Balancer
$tabLB = New-Object System.Windows.Forms.TabPage
$tabLB.Text = "Load Balancer"
$tabLB.BackColor = [System.Drawing.Color]::FromArgb(20, 30, 40)
$tabLB.ForeColor = [System.Drawing.Color]::White
$tabControl.Controls.Add($tabLB)

$lblLBResource = New-Object System.Windows.Forms.Label
$lblLBResource.Text = "Resource Type:"
$lblLBResource.Location = New-Object System.Drawing.Point(10, 20)
$lblLBResource.ForeColor = [System.Drawing.Color]::White
$tabLB.Controls.Add($lblLBResource)

$cmbLBResource = New-Object System.Windows.Forms.ComboBox
$cmbLBResource.Location = New-Object System.Drawing.Point(120, 17)
$cmbLBResource.Size = New-Object System.Drawing.Size(150, 25)
$cmbLBResource.Items.AddRange(@("CPU", "Memory", "Network"))
$cmbLBResource.SelectedIndex = 0
$tabLB.Controls.Add($cmbLBResource)

$btnCheckLB = New-Object System.Windows.Forms.Button
$btnCheckLB.Text = "Check Load"
$btnCheckLB.Location = New-Object System.Drawing.Point(280, 17)
$btnCheckLB.Size = New-Object System.Drawing.Size(120, 25)
$tabLB.Controls.Add($btnCheckLB)

$txtLBInfo = New-Object System.Windows.Forms.TextBox
$txtLBInfo.Location = New-Object System.Drawing.Point(10, 55)
$txtLBInfo.Size = New-Object System.Drawing.Size(1020, 400)
$txtLBInfo.BackColor = [System.Drawing.Color]::FromArgb(40, 50, 60)
$txtLBInfo.ForeColor = [System.Drawing.Color]::White
$txtLBInfo.Multiline = $true
$tabLB.Controls.Add($txtLBInfo)

# Functions
function Get-SystemStats {
    try {
        $cpu = Get-WmiObject Win32_Processor | Measure-Object -Property LoadPercentage -Average | Select-Object -ExpandProperty Average
        $mem = Get-WmiObject Win32_ComputerSystem
        $memUsed = (Get-WmiObject Win32_OperatingSystem).TotalVisibleMemorySize - (Get-WmiObject Win32_OperatingSystem).FreePhysicalMemory
        $memTotal = $mem.TotalPhysicalMemory
        $memUsage = [math]::Round(($memUsed / $memTotal) * 100, 2)
        
        $diskInfo = ""
        Get-WmiObject Win32_LogicalDisk | Where-Object {$_.DriveType -eq 3} | ForEach-Object {
            $diskInfo += "Drive $($_.DeviceID): $([math]::Round($_.FreeSpace / 1GB, 2))GB free of $([math]::Round($_.Size / 1GB, 2))GB`n"
        }
        
        return @{
            CPU = $cpu
            Memory = $memUsage
            DiskInfo = $diskInfo
        }
    } catch {
        return @{ CPU = 0; Memory = 0; DiskInfo = "Error getting stats" }
    }
}

function Compress-Logs {
    param($Source, $Name)
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $dest = "/home/manoj/DevWorkspaces/storage/compressed/${Name}_${timestamp}.7z"
    
    # Create directory if not exists
    New-Item -ItemType Directory -Force -Path "/home/manoj/DevWorkspaces/storage/compressed" | Out-Null
    
    $lblCompressionResult.Text = "Compressing $Source to $dest..."
    $lblCompressionResult.Update()
    
    # Use bash for compression
    $result = bash -c "cd /home/manoj/DevWorkspaces && 7z a -t7z '$dest' '$Source' -mx=9 2>&1" 2>&1
    if ($LASTEXITCODE -ne 0) {
        # Fallback to tar.gz
        $dest = "/home/manoj/DevWorkspaces/storage/compressed/${Name}_${timestamp}.tar.gz"
        $result = bash -c "tar -czf '$dest' -C /home/manoj/DevWorkspaces logs 2>&1"
    }
    
    $lblCompressionResult.Text = "Compression complete: $dest`n$result"
}

# Event Handlers
$timer = New-Object System.Windows.Forms.Timer
$timer.Interval = 2000
$timer.Add_Tick({
    $stats = Get-SystemStats
    $progressCPU.Value = $stats.CPU
    $lblCPUValue.Text = "$($stats.CPU)%"
    $progressMem.Value = $stats.Memory
    $lblMemValue.Text = "$($stats.Memory)%"
    $txtDiskInfo.Text = $stats.DiskInfo
})
$timer.Start()

$btnCompress.Add_Click({
    Compress-Logs -Source $txtLogSource.Text -Name $txtArchiveName.Text
})

$btnStoreWS.Add_Click({
    $wsId = $txtWSId.Text
    if ($wsId) {
        $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
        $data = @{ ConnectionId = $wsId; Data = "Test data"; Timestamp = $timestamp }
        $data | ConvertTo-Json | Out-File -FilePath "/home/manoj/DevWorkspaces/storage/ws_cache/${wsId}_${timestamp}.json" -Encoding UTF8
        $txtWSInfo.Text += "Stored WS data for $wsId at $timestamp`n"
    }
})

$btnRefreshStorage.Add_Click({
    $path = $txtStoragePath.Text
    if (Test-Path $path.Replace("/home/manoj/DevWorkspaces", "/mnt/c/Users/Acer/Desktop/DevWorkspaces")) {
        $info = bash -c "ls -lah '$path' 2>&1"
        $txtStorageInfo.Text = $info
    } else {
        $txtStorageInfo.Text = "Path not found: $path"
    }
})

$btnExecuteWSL.Add_Click({
    $cmd = $txtWSLCommand.Text
    $output = bash -c "$cmd 2>&1"
    $txtWSLOutput.Text = $output
})

$btnCheckLB.Add_Click({
    $resource = $cmbLBResource.Text
    $stats = Get-SystemStats
    $txtLBInfo.Text = "Load Balancer Status for: $resource`n"
    $txtLBInfo.Text += "Current Load: $($stats.$resource)`n"
    $txtLBInfo.Text += "Recommendation: "
    switch($resource) {
        "CPU" { 
            if ($stats.CPU -gt 80) { $txtLBInfo.Text += "High load - scale out recommended" }
            elseif ($stats.CPU -gt 50) { $txtLBInfo.Text += "Medium load - monitor closely" }
            else { $txtLBInfo.Text += "Low load - can handle more requests" }
        }
        "Memory" {
            if ($stats.Memory -gt 80) { $txtLBInfo.Text += "High memory usage - free resources" }
            elseif ($stats.Memory -gt 50) { $txtLBInfo.Text += "Moderate memory usage" }
            else { $txtLBInfo.Text += "Memory is healthy" }
        }
        default { $txtLBInfo.Text += "Status normal" }
    }
})

$form.ShowDialog()
