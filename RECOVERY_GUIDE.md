# 🔄 Complete System Recovery Guide
## Restore Everything on Your New Ubuntu Laptop

---

## 📋 **Recovery Overview**
Your complete system backup is stored in GitHub repository: **https://github.com/Manoj-548/DevWorkspaces**

The backup includes:
- ✅ All development projects and code
- ✅ Windows Desktop files and shortcuts
- ✅ Windows Documents and PowerShell profiles
- ✅ System configurations and settings
- ✅ Installed applications list
- ✅ Browser bookmarks and data

---

## 🚀 **Step-by-Step Recovery Process**

### **Phase 1: Initial Setup on New Ubuntu Laptop**

#### 1. Install Ubuntu and Basic Tools
```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install essential tools
sudo apt-get install -y git curl wget python3 python3-pip python3-venv
sudo apt-get install -y build-essential software-properties-common
```

#### 2. Install Git and Clone Repository
```bash
# Install Git (if not already installed)
sudo apt-get install -y git

# Clone your backup repository
git clone https://github.com/Manoj-548/DevWorkspaces.git
cd DevWorkspaces
```

#### 3. Run Automated Restore Script
```bash
# Make scripts executable
chmod +x backup_restore.sh
chmod +x complete_system_backup.sh

# Run the restore script
./backup_restore.sh
# Select option 5: "Full setup (restore + environment + dependencies)"
```

---

### **Phase 2: Manual Recovery Steps**

#### **Option A: Automated Full Restore (Recommended)**
```bash
# This will:
# 1. Install all system dependencies
# 2. Set up Python environment
# 3. Install all Python packages
# 4. Restore configurations
./backup_restore.sh
# Choose option 5
```

#### **Option B: Manual Step-by-Step Restore**

##### **Step 1: Install System Dependencies**
```bash
# Install Docker
sudo apt-get install -y docker.io docker-compose
sudo systemctl start docker
sudo systemctl enable docker

# Install development tools
sudo apt-get install -y nodejs npm
sudo apt-get install -y postgresql postgresql-contrib  # If using PostgreSQL
sudo apt-get install -y redis-server  # If using Redis
```

##### **Step 2: Restore Python Environment**
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install all project dependencies
find . -name "requirements.txt" -type f -exec pip install -r {} \;

# Deactivate when done
deactivate
```

##### **Step 3: Restore VS Code Settings**
```bash
# VS Code settings are backed up in: backup/system_config/vscode/
# Copy settings.json and keybindings.json to:
# ~/.config/Code/User/ (on Linux)
```

##### **Step 4: Restore SSH Keys (IMPORTANT!)**
```bash
# If you had SSH keys backed up:
mkdir -p ~/.ssh
chmod 700 ~/.ssh

# Copy SSH keys from backup/system_config/ssh_keys/
# Set proper permissions:
chmod 600 ~/.ssh/id_rsa
chmod 644 ~/.ssh/id_rsa.pub
```

---

### **Phase 3: Restore Windows-Specific Data**

#### **Desktop Shortcuts and Files**
Your Windows Desktop files are backed up in `backup/windows_desktop/`:
- DevDashboard shortcuts and scripts
- Office setup files
- Application shortcuts

#### **Documents and PowerShell Profiles**
Windows Documents are backed up in `backup/windows_documents/`:
- PowerShell profiles and scripts
- Datasets and project files

#### **Browser Bookmarks**
- Chrome bookmarks: `backup/browser_data/chrome_bookmarks.json`
- Firefox data: `backup/browser_data/firefox_places.sqlite`

---

### **Phase 4: Restore Applications**

#### **Check Backed Up Applications List**
```bash
# View installed applications from backup
cat backup/system_info/wsl_packages.txt      # WSL packages
cat backup/system_info/windows_apps.csv      # Windows apps
cat backup/system_info/windows_programs.csv  # Windows programs
```

#### **Reinstall Key Applications**
```bash
# Install from the backed up list
sudo apt-get install -y git curl wget python3 python3-pip
sudo apt-get install -y docker.io docker-compose
sudo apt-get install -y nodejs npm
sudo apt-get install -y code  # VS Code
sudo apt-get install -y google-chrome-stable  # Chrome
```

---

### **Phase 5: Restore Development Projects**

#### **All Projects Are Ready**
Your projects are fully backed up and ready:
- `projects/comprehensive-dashboard/` - Main dashboard
- `projects/python-dashboard/` - Django dashboard
- `projects/devops-dashboard/` - DevOps tools
- `projects/yolov8-poc/` - ML project
- `services/` - All microservices

#### **Start Development Environment**
```bash
# Activate virtual environment
source venv/bin/activate

# Start services
cd services/realtime_api && python main.py &
cd projects/comprehensive-dashboard && python app.py &

# Or use Docker Compose
docker-compose up -d
```

---

## 🔧 **Troubleshooting Recovery**

### **Common Issues & Solutions**

#### **1. Permission Issues**
```bash
# Fix script permissions
chmod +x *.sh
chmod +x scripts/*.sh
```

#### **2. Missing Dependencies**
```bash
# Install additional packages as needed
sudo apt-get install -y build-essential
sudo apt-get install -y libssl-dev libffi-dev python3-dev
```

#### **3. Docker Issues**
```bash
# Add user to docker group
sudo usermod -aG docker $USER
# Logout and login again, or run: newgrp docker
```

#### **4. Python Virtual Environment Issues**
```bash
# Recreate virtual environment
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
```

---

## 📁 **Backup Contents Reference**

### **GitHub Repository Structure**
```
DevWorkspaces/
├── projects/                 # All development projects
├── services/                 # Microservices and APIs
├── scripts/                  # Utility scripts
├── backup/                   # System backup data
│   ├── windows_desktop/      # Desktop files and shortcuts
│   ├── windows_documents/    # Documents and profiles
│   ├── system_info/          # Installed apps list
│   ├── browser_data/         # Bookmarks and settings
│   └── system_config/        # Config files and SSH keys
├── backup_restore.sh         # Automated restore script
└── complete_system_backup.sh # Backup script
```

### **External Backup Needed**
For large files not in GitHub, follow `backup/EXTERNAL_BACKUP_GUIDE.md`

---

## ✅ **Verification Checklist**

After recovery, verify:
- [ ] GitHub repository cloned successfully
- [ ] Python virtual environment working
- [ ] All projects can run
- [ ] Docker services start
- [ ] VS Code extensions installed
- [ ] SSH keys restored (if any)
- [ ] Browser bookmarks imported

---

## 🎯 **Quick Start Commands**

```bash
# One-command full restore (recommended)
git clone https://github.com/Manoj-548/DevWorkspaces.git
cd DevWorkspaces
chmod +x backup_restore.sh
./backup_restore.sh
# Select option 5

# Quick verification
source venv/bin/activate
python --version
pip list | head -10
```

---

## 📞 **Need Help?**

If you encounter issues:
1. Check the backup logs in terminal output
2. Verify all scripts have execute permissions
3. Ensure you're running commands from the correct directory
4. Check `backup/EXTERNAL_BACKUP_GUIDE.md` for large files

**Your complete development environment will be restored! 🚀**
