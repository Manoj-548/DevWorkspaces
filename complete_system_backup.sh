#!/bin/bash

# ================================================
# Complete System Backup Script
# Backs up all data from WSL and Windows
# ================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔄 Complete System Backup Script${NC}"
echo "======================================"

# Function to backup WSL data to GitHub
backup_wsl_to_github() {
    echo -e "${YELLOW}📦 Backing up WSL data to GitHub...${NC}"

    # Add all changes
    git add .

    # Commit with timestamp
    git commit -m "Complete system backup: $(date '+%Y-%m-%d %H:%M:%S')"

    # Push to GitHub
    git push origin main

    echo -e "${GREEN}✅ WSL data backed up to GitHub!${NC}"
}

# Function to backup Windows Desktop files
backup_windows_desktop() {
    echo -e "${YELLOW}🖥️  Backing up Windows Desktop files...${NC}"

    # Windows Desktop path in WSL
    WINDOWS_DESKTOP="/mnt/c/Users/Acer/Desktop"

    if [ -d "$WINDOWS_DESKTOP" ]; then
        echo "Copying Desktop files to backup directory..."
        mkdir -p backup/windows_desktop
        cp -r "$WINDOWS_DESKTOP"/* backup/windows_desktop/ 2>/dev/null || true

        # Add to git
        git add backup/windows_desktop
        git commit -m "Windows Desktop backup: $(date '+%Y-%m-%d %H:%M:%S')" || true
        git push origin main || true

        echo -e "${GREEN}✅ Windows Desktop files backed up!${NC}"
    else
        echo -e "${RED}❌ Windows Desktop not found at $WINDOWS_DESKTOP${NC}"
    fi
}

# Function to backup Windows Documents
backup_windows_documents() {
    echo -e "${YELLOW}📄 Backing up Windows Documents...${NC}"

    WINDOWS_DOCS="/mnt/c/Users/Acer/Documents"

    if [ -d "$WINDOWS_DOCS" ]; then
        echo "Copying Documents files to backup directory..."
        mkdir -p backup/windows_documents
        cp -r "$WINDOWS_DOCS"/* backup/windows_documents/ 2>/dev/null || true

        # Add to git (if not too large)
        if [ $(du -sm backup/windows_documents | cut -f1) -lt 100 ]; then
            git add backup/windows_documents
            git commit -m "Windows Documents backup: $(date '+%Y-%m-%d %H:%M:%S')" || true
            git push origin main || true
            echo -e "${GREEN}✅ Windows Documents backed up to GitHub!${NC}"
        else
            echo -e "${YELLOW}⚠️  Documents folder too large for GitHub. Consider external backup.${NC}"
        fi
    else
        echo -e "${RED}❌ Windows Documents not found at $WINDOWS_DOCS${NC}"
    fi
}

# Function to backup installed applications list
backup_installed_apps() {
    echo -e "${YELLOW}📱 Backing up installed applications list...${NC}"

    mkdir -p backup/system_info

    # Get WSL installed packages
    echo "Getting WSL package list..."
    dpkg --get-selections > backup/system_info/wsl_packages.txt

    # Get Windows installed apps (using PowerShell via WSL)
    echo "Getting Windows installed apps..."
    powershell.exe -Command "Get-AppxPackage | Select Name, PackageFullName, Version | ConvertTo-Csv" > backup/system_info/windows_apps.csv 2>/dev/null || true

    # Get Windows installed programs
    echo "Getting Windows installed programs..."
    powershell.exe -Command "Get-ItemProperty HKLM:\\Software\\Wow6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\* | Select DisplayName, DisplayVersion, Publisher | ConvertTo-Csv" > backup/system_info/windows_programs.csv 2>/dev/null || true

    # Add to git
    git add backup/system_info
    git commit -m "System applications backup: $(date '+%Y-%m-%d %H:%M:%S')" || true
    git push origin main || true

    echo -e "${GREEN}✅ Applications list backed up!${NC}"
}

# Function to backup browser data
backup_browser_data() {
    echo -e "${YELLOW}🌐 Backing up browser bookmarks and settings...${NC}"

    mkdir -p backup/browser_data

    # Chrome bookmarks (if accessible)
    CHROME_BOOKMARKS="/mnt/c/Users/Acer/AppData/Local/Google/Chrome/User Data/Default/Bookmarks"
    if [ -f "$CHROME_BOOKMARKS" ]; then
        cp "$CHROME_BOOKMARKS" backup/browser_data/chrome_bookmarks.json
        echo "Chrome bookmarks backed up"
    fi

    # Firefox profiles (if accessible)
    FIREFOX_PROFILES="/mnt/c/Users/Acer/AppData/Roaming/Mozilla/Firefox/Profiles"
    if [ -d "$FIREFOX_PROFILES" ]; then
        find "$FIREFOX_PROFILES" -name "places.sqlite" -exec cp {} backup/browser_data/firefox_places.sqlite \; 2>/dev/null || true
        echo "Firefox bookmarks backed up"
    fi

    # Add to git
    git add backup/browser_data
    git commit -m "Browser data backup: $(date '+%Y-%m-%d %H:%M:%S')" || true
    git push origin main || true

    echo -e "${GREEN}✅ Browser data backed up!${NC}"
}

# Function to create system configuration backup
backup_system_config() {
    echo -e "${YELLOW}⚙️  Backing up system configuration...${NC}"

    mkdir -p backup/system_config

    # WSL configuration
    cp ~/.bashrc backup/system_config/bashrc 2>/dev/null || true
    cp ~/.bash_profile backup/system_config/bash_profile 2>/dev/null || true
    cp ~/.gitconfig backup/system_config/gitconfig 2>/dev/null || true

    # SSH keys (if any)
    if [ -d ~/.ssh ]; then
        cp -r ~/.ssh backup/system_config/ssh_keys
        echo "SSH keys backed up (remember to secure these!)"
    fi

    # VS Code settings
    VSCODE_SETTINGS="/mnt/c/Users/Acer/AppData/Roaming/Code/User"
    if [ -d "$VSCODE_SETTINGS" ]; then
        mkdir -p backup/system_config/vscode
        cp "$VSCODE_SETTINGS/settings.json" backup/system_config/vscode/ 2>/dev/null || true
        cp "$VSCODE_SETTINGS/keybindings.json" backup/system_config/vscode/ 2>/dev/null || true
    fi

    # Add to git
    git add backup/system_config
    git commit -m "System configuration backup: $(date '+%Y-%m-%d %H:%M:%S')" || true
    git push origin main || true

    echo -e "${GREEN}✅ System configuration backed up!${NC}"
}

# Function to create external drive backup instructions
create_external_backup_guide() {
    echo -e "${YELLOW}💾 Creating external backup guide...${NC}"

    cat > backup/EXTERNAL_BACKUP_GUIDE.md << 'EOF'
# External Backup Guide
# For large files and complete system backup

## Important Directories to Backup Externally:
- C:\Users\Acer\Desktop\*
- C:\Users\Acer\Documents\*
- C:\Users\Acer\Downloads\*
- C:\Users\Acer\Pictures\*
- C:\Users\Acer\Videos\*
- C:\Users\Acer\Music\*

## Application Data:
- C:\Users\Acer\AppData\*
- C:\Program Files\*
- C:\Program Files (x86)\*

## Using Windows Backup:
1. Open Settings > Update & Security > Backup
2. Add a drive for backup
3. Run backup

## Using External Tools:
- Macrium Reflect (free for personal use)
- Acronis True Image
- Windows built-in backup

## Cloud Backup Options:
- OneDrive
- Google Drive
- Dropbox
- External hard drive

EOF

    git add backup/EXTERNAL_BACKUP_GUIDE.md
    git commit -m "External backup guide added" || true
    git push origin main || true

    echo -e "${GREEN}✅ External backup guide created!${NC}"
}

# Function to run complete backup
complete_backup() {
    echo -e "${BLUE}🚀 Starting Complete System Backup${NC}"
    echo "=================================="

    # Create backup directory
    mkdir -p backup

    # Run all backup functions
    backup_wsl_to_github
    backup_windows_desktop
    backup_windows_documents
    backup_installed_apps
    backup_browser_data
    backup_system_config
    create_external_backup_guide

    echo -e "${GREEN}🎉 Complete backup finished!${NC}"
    echo "=================================="
    echo "Your data is now backed up to:"
    echo "- GitHub: https://github.com/Manoj-548/DevWorkspaces"
    echo "- Local backup folder: ./backup/"
    echo ""
    echo "For large files, follow EXTERNAL_BACKUP_GUIDE.md"
}

# Display menu
echo "Complete System Backup Options:"
echo "1. Complete backup (all data)"
echo "2. WSL data only"
echo "3. Windows Desktop only"
echo "4. Windows Documents only"
echo "5. Applications list only"
echo "6. Browser data only"
echo "7. System configuration only"
echo "8. Create external backup guide"

read -p "Enter option (1-8): " option

case $option in
    1)
        complete_backup
        ;;
    2)
        backup_wsl_to_github
        ;;
    3)
        backup_windows_desktop
        ;;
    4)
        backup_windows_documents
        ;;
    5)
        backup_installed_apps
        ;;
    6)
        backup_browser_data
        ;;
    7)
        backup_system_config
        ;;
    8)
        create_external_backup_guide
        ;;
    *)
        echo -e "${RED}Invalid option!${NC}"
        exit 1
        ;;
esac

echo "=================================="
echo -e "${GREEN}Backup operations completed!${NC}"
echo ""
echo "Next steps:"
echo "1. Review backed up data on GitHub"
echo "2. Follow EXTERNAL_BACKUP_GUIDE.md for large files"
echo "3. Test restore on new system using backup_restore.sh"
