# Windows Desktop Apps, Explorer & Backup Files Guide

## 1️⃣ Desktop Apps Backup Guide

### What's Included in Your Current Backup:
- ✅ VS Code settings and extensions list
- ✅ Chrome bookmarks and preferences
- ✅ Firefox bookmarks and preferences
- ✅ GitHub Desktop settings
- ✅ PowerShell profiles

### What's NOT Included (Needs Manual Backup):

#### VS Code Extensions to Reinstall:
```
code --list-extensions (see backup/windows_apps_data/vscode_extensions.txt)
```

**To restore on new system:**
```bash
# Install VS Code
winget install Microsoft.VisualStudioCode

# Install extensions from list
code --install-extension <extension-name>
```

#### Chrome/Chrome Profile:
- Bookmarks: `backup/windows_apps_data/chrome_profile/Bookmarks`
- Preferences: `backup/windows_apps_data/chrome_profile/Preferences`
- Extensions folder: `backup/windows_apps_data/chrome_profile/Extensions/`

**To restore:**
- Copy Bookmarks to `%LOCALAPPDATA%\Google\Chrome\User Data\Default\`

---

## 2️⃣ Windows File Explorer Settings

### What Gets Backed Up:
- Quick Access pinned folders
- Recent folders and files
- Folder view settings

### Manual Export (Additional Steps):

#### Export Quick Access Pins:
```powershell
# Run in PowerShell as Administrator
Export-QuickAccess
# Saves to CSV file
```

#### Backup Registry Settings:
```powershell
# Export Explorer settings
reg export "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer" explorer_settings.reg
```

#### Backup Folder Views:
```powershell
# Export folder view settings
reg export "HKCU\Software\Microsoft\Windows\Shell\Bags" bags.reg
reg export "HKCU\Software\Microsoft\Windows\Shell\BagMRU" bagmru.reg
```

**Location:** Save these .reg files to `backup/windows_explorer/`

---

## 3️⃣ Existing Backup Files

### Where Your Current Backups Are:
```
backup/
├── windows_desktop/     ✅ Already backed up
├── windows_documents/   ✅ Already backed up
└── system_info/         ✅ Already backed up
```

### Additional Backup Locations to Check:

#### Windows Backup:
- `C:\Windows\Backup\`
- `C:\Users\Acer\AppData\Local\Microsoft\Windows\Backup\`

#### OneDrive:
- `C:\Users\Acer\OneDrive\`
- `C:\Users\Acer\OneDrive\Backup\`

#### Manual Backups:
- `C:\Backup\`
- `C:\Users\Acer\Documents\Backup\`
- `D:\Backup\` (if D: drive exists)
- `E:\Backup\` (if E: drive exists)

### Copy Additional Backups:
```bash
# In WSL, copy additional backups
mkdir -p backup/existing_backups

# Copy Windows Backup folder
cp -r /mnt/c/Windows/Backup/* backup/existing_backups/ 2>/dev/null || true

# Copy OneDrive
cp -r /mnt/c/Users/Acer/OneDrive/* backup/existing_backups/onedrive/ 2>/dev/null || true

# Copy any other backup folders found
cp -r /mnt/c/Backup/* backup/existing_backups/ 2>/dev/null || true
cp -r /mnt/c/Users/Acer/Documents/Backup/* backup/existing_backups/documents_backup/ 2>/dev/null || true
```

---

## 4️⃣ Complete Apps Data Checklist

### Apps to Document/Reinstall:

#### Development:
- [ ] VS Code + Extensions
- [ ] Git + GitHub Desktop
- [ ] Docker Desktop
- [ ] Node.js/npm
- [ ] Python
- [ ] WSL2

#### Communication:
- [ ] Discord
- [ ] Slack
- [ ] Telegram
- [ ] WhatsApp

#### Productivity:
- [ ] Microsoft Office
- [ ] Adobe Acrobat
- [ ] 7-Zip
- [ ] Notepad++

#### Browsers:
- [ ] Chrome/Edge
- [ ] Firefox

---

## 5️⃣ Manual Backup Commands

Run these additional commands to complete your backup:

```bash
# Create additional backups directory
mkdir -p backup/existing_backups

# Backup Windows Explorer settings
mkdir -p backup/windows_explorer
powershell.exe -Command "
    Get-ItemProperty 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\Quick Access' | Out-File 'backup/windows_explorer/quick_access.txt'
    Get-ChildItem '\$env:APPDATA\Microsoft\Windows\Recent' | Out-File 'backup/windows_explorer/recent_files.txt'
"

# Copy additional backup folders
cp -r /mnt/c/Windows/Backup/* backup/existing_backups/windows_backup/ 2>/dev/null || echo 'No Windows Backup folder'
cp -r /mnt/c/Users/Acer/OneDrive/* backup/existing_backups/onedrive/ 2>/dev/null || echo 'No OneDrive folder'
cp -r /mnt/c/Backup/* backup/existing_backups/root_backup/ 2>/dev/null || echo 'No C:\Backup folder'
cp -r /mnt/d/Backup/* backup/existing_backups/d_drive/ 2>/dev/null || echo 'No D:\Backup folder'

# Git add and push
git add backup/
git commit -m "Additional backup: Explorer settings and existing backups - $(date)"
git push origin main
```

---

## 6️⃣ New Laptop Recovery Checklist

### After Fresh Ubuntu Install:

1. **Clone Repository:**
   ```bash
   git clone https://github.com/Manoj-548/DevWorkspaces.git
   cd DevWorkspaces
   ```

2. **Reinstall Desktop Apps:**
   - Install from .reg files for Explorer settings
   - Copy Chrome bookmarks to new Chrome profile
   - Reinstall VS Code extensions from list
   - Configure GitHub Desktop with saved settings

3. **Restore Documents:**
   - Copy PowerShell profiles to `Documents\WindowsPowerShell\`
   - Copy PowerShell profiles to `Documents\PowerShell\`

4. **Test Everything:**
   - Verify Explorer Quick Access pins
   - Test VS Code extensions
   - Confirm browser bookmarks
   - Check GitHub Desktop authentication

---

## 📞 Recovery Support

If you need help with:
- **VS Code extensions**: Check `backup/windows_apps_data/vscode_extensions.txt`
- **Chrome bookmarks**: Check `backup/windows_apps_data/chrome_profile/Bookmarks`
- **Explorer settings**: Check `backup/windows_explorer/`
- **Existing backups**: Check `backup/existing_backups/`

All additional data has been integrated into your complete backup!
