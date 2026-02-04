# DevDashboard helpers - auto-sourced
function dev {
    param([string] = 'ui')
    switch () {
        'ui' { Start-Process -FilePath (Join-Path 'C:\Users\Acer\Desktop\DevDashboard' 'dashboard.html'); break }
        'update' { Write-Host 'No remote configured for updates (edit devos_selfupdate.ps1)'; break }
        'ws' { code \\wsl$\Ubuntu\home\manoj\DevWorkspaces; break }
        'docker' { wsl -d Ubuntu -- bash -lc 'bash ~/.devos/docker_manager.sh'; break }
        'gpu' { wsl -d Ubuntu -- bash -lc 'bash ~/.devos/gpu_monitor.sh'; break }
        'git' { wsl -d Ubuntu -- bash -lc 'bash ~/.devos/git_templates.sh'; break }
        default { Write-Host 'Available: dev [ui|update|ws|docker|gpu|git]' -ForegroundColor Cyan }
    }
}
Set-Alias vd-code dev
Set-Alias vd-docker dev
Set-Alias vd-gpu dev
Set-Alias vd-git dev
