# DevDashboard PowerShell GUI
# Run this script to open the dashboard GUI

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$form = New-Object System.Windows.Forms.Form
$form.Text = "DevDashboard - Vindash"
$form.Size = New-Object System.Drawing.Size(500,400)
$form.StartPosition = "CenterScreen"
$form.BackColor = [System.Drawing.Color]::FromArgb(15,23,32)

$font = New-Object System.Drawing.Font("Arial",10,[System.Drawing.FontStyle]::Regular)

$button1 = New-Object System.Windows.Forms.Button
$button1.Location = New-Object System.Drawing.Point(20,20)
$button1.Size = New-Object System.Drawing.Size(200,40)
$button1.Text = "Open DevWorkspaces (VS Code)"
$button1.Font = $font
$button1.BackColor = [System.Drawing.Color]::FromArgb(0,102,204)
$button1.ForeColor = [System.Drawing.Color]::White
$button1.Add_Click({
    Start-Process "vscode://file/home/manoj/DevWorkspaces"
})
$form.Controls.Add($button1)

$button2 = New-Object System.Windows.Forms.Button
$button2.Location = New-Object System.Drawing.Point(20,70)
$button2.Size = New-Object System.Drawing.Size(200,40)
$button2.Text = "Open Vindash (WSL Terminal)"
$button2.Font = $font
$button2.BackColor = [System.Drawing.Color]::FromArgb(0,102,204)
$button2.ForeColor = [System.Drawing.Color]::White
$button2.Add_Click({
    $cmd = 'wsl.exe -d Ubuntu -- bash -lc "source /home/manoj/.vindashrc; cd /home/manoj/DevWorkspaces; bash"'
    Start-Process "wsl.exe" -ArgumentList "-d Ubuntu -- bash -lc `"source /home/manoj/.vindashrc; cd /home/manoj/DevWorkspaces; bash`""
})
$form.Controls.Add($button2)

$button3 = New-Object System.Windows.Forms.Button
$button3.Location = New-Object System.Drawing.Point(20,120)
$button3.Size = New-Object System.Drawing.Size(200,40)
$button3.Text = "Start Django"
$button3.Font = $font
$button3.BackColor = [System.Drawing.Color]::FromArgb(0,102,204)
$button3.ForeColor = [System.Drawing.Color]::White
$button3.Add_Click({
    Start-Process "wsl.exe" -ArgumentList "-d Ubuntu bash -l -c `"cd /home/manoj/DevWorkspaces/DjangoService; source venv/bin/activate; python3 manage.py runserver 0.0.0.0:8000`""
})
$form.Controls.Add($button3)

$button4 = New-Object System.Windows.Forms.Button
$button4.Location = New-Object System.Drawing.Point(250,20)
$button4.Size = New-Object System.Drawing.Size(200,40)
$button4.Text = "Docker Manager"
$button4.Font = $font
$button4.BackColor = [System.Drawing.Color]::FromArgb(0,102,204)
$button4.ForeColor = [System.Drawing.Color]::White
$button4.Add_Click({
    Start-Process "wsl.exe" -ArgumentList "-d Ubuntu bash -l -c `"bash /home/manoj/.devos/docker_manager.sh`""
})
$form.Controls.Add($button4)

$button5 = New-Object System.Windows.Forms.Button
$button5.Location = New-Object System.Drawing.Point(250,70)
$button5.Size = New-Object System.Drawing.Size(200,40)
$button5.Text = "GPU Monitor"
$button5.Font = $font
$button5.BackColor = [System.Drawing.Color]::FromArgb(0,102,204)
$button5.ForeColor = [System.Drawing.Color]::White
$button5.Add_Click({
    Start-Process "wsl.exe" -ArgumentList "-d Ubuntu bash -l -c `"bash /home/manoj/.devos/gpu_monitor.sh`""
})
$form.Controls.Add($button5)

$button6 = New-Object System.Windows.Forms.Button
$button6.Location = New-Object System.Drawing.Point(250,120)
$button6.Size = New-Object System.Drawing.Size(200,40)
$button6.Text = "Git Templates and PR Flow"
$button6.Font = $font
$button6.BackColor = [System.Drawing.Color]::FromArgb(0,102,204)
$button6.ForeColor = [System.Drawing.Color]::White
$button6.Add_Click({
    Start-Process "wsl.exe" -ArgumentList "-d Ubuntu bash -l -c `"bash /home/manoj/.devos/git_templates.sh`""
})
$form.Controls.Add($button6)

$button7 = New-Object System.Windows.Forms.Button
$button7.Location = New-Object System.Drawing.Point(20,170)
$button7.Size = New-Object System.Drawing.Size(200,40)
$button7.Text = "ML Tools (Jupyter)"
$button7.Font = $font
$button7.BackColor = [System.Drawing.Color]::FromArgb(0,102,204)
$button7.ForeColor = [System.Drawing.Color]::White
$button7.Add_Click({
    Start-Process "wsl.exe" -ArgumentList "-d Ubuntu bash -l -c `"cd /home/manoj/DevWorkspaces/ModelBuilding; jupyter lab --no-browser --ip=0.0.0.0`""
})
$form.Controls.Add($button7)

$form.ShowDialog()

