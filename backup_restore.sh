#!/bin/bash

# ================================================
# DevWorkspaces Backup & Restore Script
# For transferring to new Ubuntu laptop
# ================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 DevWorkspaces Backup & Restore Script${NC}"
echo "============================================"

# Function to backup to GitHub
backup_to_github() {
    echo -e "${YELLOW}📦 Backing up to GitHub...${NC}"
    
    # Add all changes
    git add .
    
    # Commit with timestamp
    git commit -m "Backup: $(date '+%Y-%m-%d %H:%M:%S')"
    
    # Push to GitHub
    git push origin main
    
    echo -e "${GREEN}✅ Backup completed successfully!${NC}"
}

# Function to restore from GitHub
restore_from_github() {
    echo -e "${YELLOW}📥 Restoring from GitHub...${NC}"
    
    # Clone repository
    if [ -d "DevWorkspaces" ]; then
        echo "Directory already exists. Pulling latest changes..."
        cd DevWorkspaces
        git pull origin main
    else
        git clone https://github.com/Manoj-548/DevWorkspaces.git
        cd DevWorkspaces
    fi
    
    echo -e "${GREEN}✅ Restore completed successfully!${NC}"
}

# Function to setup development environment
setup_environment() {
    echo -e "${YELLOW}🔧 Setting up development environment...${NC}"
    
    # Update system
    sudo apt-get update && sudo apt-get upgrade -y
    
    # Install Python and pip
    sudo apt-get install -y python3 python3-pip python3-venv
    
    # Install Docker
    sudo apt-get install -y docker.io docker-compose
    sudo systemctl start docker
    sudo systemctl enable docker
    
    # Install Git
    sudo apt-get install -y git
    
    echo -e "${GREEN}✅ Environment setup completed!${NC}"
}

# Function to install all Python dependencies
install_dependencies() {
    echo -e "${YELLOW}📚 Installing Python dependencies...${NC}"
    
    # Create virtual environment
    python3 -m venv venv
    source venv/bin/activate
    
    # Install requirements for each project
    find . -name "requirements.txt" -type f -exec pip install -r {} \;
    
    deactivate
    
    echo -e "${GREEN}✅ Dependencies installed successfully!${NC}"
}

# Function to run full setup
full_setup() {
    echo -e "${YELLOW}🔄 Running full setup...${NC}"
    
    restore_from_github
    setup_environment
    install_dependencies
    
    echo -e "${GREEN}✅ Full setup completed!${NC}"
}

# Display menu
echo "Please choose an option:"
echo "1. Backup to GitHub (on current laptop)"
echo "2. Restore from GitHub (on new Ubuntu laptop)"
echo "3. Setup development environment"
echo "4. Install dependencies"
echo "5. Full setup (restore + environment + dependencies)"
echo "6. Quick restore (just clone and install)"

read -p "Enter option (1-6): " option

case $option in
    1)
        backup_to_github
        ;;
    2)
        restore_from_github
        ;;
    3)
        setup_environment
        ;;
    4)
        install_dependencies
        ;;
    5)
        full_setup
        ;;
    6)
        restore_from_github
        install_dependencies
        ;;
    *)
        echo -e "${RED}Invalid option!${NC}"
        exit 1
        ;;
esac

echo "============================================"
echo -e "${GREEN}Done!${NC}"

